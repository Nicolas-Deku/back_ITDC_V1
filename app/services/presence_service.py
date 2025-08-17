from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
import logging

from app.models import PresenceDB, EmployeDB
from app.schemas.schemas import PresenceCreate, PresenceResponse
from app.repositories.presence_repository import PresenceRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PresenceService:
    def __init__(self, db: Session):
        self.db = db
        self.presence_repo = PresenceRepository(db)

    def create_presence(self, presence_data: PresenceCreate, current_user: EmployeDB) -> PresenceResponse:
        """
        Crée une nouvelle présence pour un employé.

        Args:
            presence_data: Données de la présence.
            current_user: Utilisateur authentifié (manager/admin).

        Returns:
            PresenceResponse: Détails de la présence créée.

        Raises:
            HTTPException: Si l'employé n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        if current_user.role not in ["admin", "manager"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à créer une présence.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les admins ou managers peuvent créer une présence."
            )
        employe = self.db.query(EmployeDB).filter(EmployeDB.idEmploye == presence_data.idEmploye).first()
        if not employe:
            logger.error(f"Employé avec ID {presence_data.idEmploye} non trouvé.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")
        if current_user.idEntreprise != employe.idEntreprise:
            logger.error(f"Utilisateur {current_user.email} n'appartient pas à l'entreprise de l'employé {presence_data.idEmploye}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à créer une présence pour cet employé."
            )
        db_presence = self.presence_repo.create_presence(presence_data.dict(exclude_unset=True), employe)
        return PresenceResponse.from_orm(db_presence)

    def get_presence(self, presence_id: UUID, current_user: EmployeDB) -> PresenceResponse:
        """
        Récupère une présence par son ID.

        Args:
            presence_id: ID de la présence.
            current_user: Utilisateur authentifié (tous les rôles).

        Returns:
            PresenceResponse: Détails de la présence.

        Raises:
            HTTPException: Si la présence n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        presence = self.presence_repo.get_presence_by_id(presence_id)
        if not presence:
            logger.error(f"Présence avec ID {presence_id} non trouvée.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Présence non trouvée")
        if str(current_user.idEmploye) != str(presence.idEmploye) and current_user.role not in ["admin", "manager"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à accéder à la présence {presence_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à voir cette présence."
            )
        return PresenceResponse.from_orm(presence)

    def list_presences(self, current_user: EmployeDB, skip: int = 0, limit: int = 100) -> List[PresenceResponse]:
        """
        Liste toutes les présences avec pagination.

        Args:
            current_user: Utilisateur authentifié (manager/admin).
            skip: Nombre d'éléments à ignorer.
            limit: Nombre maximal d'éléments à retourner.

        Returns:
            List[PresenceResponse]: Liste des présences.
        """
        if current_user.role not in ["admin", "manager"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à lister les présences.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les admins ou managers peuvent lister les présences."
            )
        presences = self.presence_repo.list_presences(skip, limit)
        return [PresenceResponse.from_orm(p) for p in presences]

    def delete_presence(self, presence_id: UUID, current_user: EmployeDB):
        """
        Supprime une présence.

        Args:
            presence_id: ID de la présence.
            current_user: Utilisateur authentifié (admin).

        Raises:
            HTTPException: Si la présence n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        if current_user.role != "admin":
            logger.error(f"Utilisateur {current_user.email} non autorisé à supprimer la présence {presence_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seul un admin peut supprimer une présence."
            )
        db_presence = self.presence_repo.get_presence_by_id(presence_id)
        if not db_presence:
            logger.error(f"Présence avec ID {presence_id} non trouvée.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Présence non trouvée")
        self.presence_repo.delete_presence(db_presence)
        logger.info(f"Présence {presence_id} supprimée par {current_user.email}")