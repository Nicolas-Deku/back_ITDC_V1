from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models import PresenceDB, EmployeDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PresenceRepository:
    """
    Gère les opérations de persistance des données pour les présences.
    """
    def __init__(self, db: Session):
        self.db = db

    def create_presence(self, presence_data: dict, employe: EmployeDB) -> PresenceDB:
        """
        Crée une nouvelle présence pour un employé.

        Args:
            presence_data: Données de la présence.
            employe: Employé associé à la présence.

        Returns:
            PresenceDB: Présence créée.
        """
        db_presence = PresenceDB(
            idEmploye=employe.idEmploye,
            timestamp=presence_data.get("timestamp", datetime.now()),
            type=presence_data["type"],
            methode=presence_data.get("methode", "manuel"),
            appareil_id=presence_data.get("appareil_id"),
            notes=presence_data.get("notes"),
            statut=presence_data.get("statut", "valide")
        )
        self.db.add(db_presence)
        self.db.commit()
        self.db.refresh(db_presence)
        logger.info(f"Présence créée pour employé {employe.email} avec ID {db_presence.idPresence}")
        return db_presence

    def get_presence_by_id(self, presence_id: UUID) -> Optional[PresenceDB]:
        """
        Récupère une présence par son ID.

        Args:
            presence_id: ID de la présence.

        Returns:
            PresenceDB: Présence trouvée ou None si non trouvée.
        """
        presence = self.db.query(PresenceDB).filter(PresenceDB.idPresence == presence_id).first()
        if presence:
            logger.info(f"Présence récupérée : {presence_id}")
        return presence

    def get_presences_by_employe_id(self, employe_id: UUID, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[PresenceDB]:
        """
        Récupère les présences d'un employé.

        Args:
            employe_id: ID de l'employé.
            start_date: Date de début pour filtrer (optionnel).
            end_date: Date de fin pour filtrer (optionnel).

        Returns:
            List[PresenceDB]: Liste des présences.
        """
        query = self.db.query(PresenceDB).filter(PresenceDB.idEmploye == employe_id)
        if start_date:
            query = query.filter(PresenceDB.timestamp >= start_date)
        if end_date:
            query = query.filter(PresenceDB.timestamp <= end_date)
        presences = query.order_by(PresenceDB.timestamp.asc()).all()
        logger.info(f"{len(presences)} présences récupérées pour employé {employe_id}")
        return presences

    def list_presences(self, skip: int = 0, limit: int = 100) -> List[PresenceDB]:
        """
        Liste toutes les présences avec pagination.

        Args:
            skip: Nombre d'éléments à ignorer.
            limit: Nombre maximal d'éléments à retourner.

        Returns:
            List[PresenceDB]: Liste des présences.
        """
        presences = self.db.query(PresenceDB).offset(skip).limit(limit).all()
        logger.info(f"{len(presences)} présences récupérées (skip={skip}, limit={limit})")
        return presences

    def delete_presence(self, presence: PresenceDB):
        """
        Supprime une présence.

        Args:
            presence: Présence à supprimer.
        """
        self.db.delete(presence)
        self.db.commit()
        logger.info(f"Présence supprimée : {presence.idPresence}")