from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models import CongeDB, EmployeDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CongeRepository:
    """
    Gère les opérations de persistance des données pour les congés.
    """
    def __init__(self, db: Session):
        self.db = db

    def create_conge(self, conge_data: Dict, employe: EmployeDB, approbateur: Optional[EmployeDB]) -> CongeDB:
        """
        Crée un nouveau congé pour un employé.

        Args:
            conge_data: Données du congé.
            employe: Employé demandant le congé.
            approbateur: Employé ayant approuvé le congé (optionnel).

        Returns:
            CongeDB: Congé créé.
        """
        db_conge = CongeDB(
            idEmploye=employe.idEmploye,
            type_conge=conge_data["type_conge"],
            date_debut=conge_data["date_debut"],
            date_fin=conge_data["date_fin"],
            statut=conge_data.get("statut", "en_attente"),
            commentaire=conge_data.get("commentaire"),
            approuve_par=approbateur.idEmploye if approbateur else None
        )
        self.db.add(db_conge)
        self.db.commit()
        self.db.refresh(db_conge)
        logger.info(f"Congé créé pour employé {employe.email} avec ID {db_conge.idConge}")
        return db_conge

    def get_conge_by_id(self, conge_id: UUID) -> Optional[CongeDB]:
        """
        Récupère un congé par son ID.

        Args:
            conge_id: ID du congé.

        Returns:
            CongeDB: Congé trouvé ou None si non trouvé.
        """
        conge = self.db.query(CongeDB).filter(CongeDB.idConge == conge_id).first()
        if conge:
            logger.info(f"Congé récupéré : {conge_id}")
        return conge

    def get_conges_by_employe_id(self, employe_id: UUID, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CongeDB]:
        """
        Récupère les congés d'un employé.

        Args:
            employe_id: ID de l'employé.
            start_date: Date de début pour filtrer (optionnel).
            end_date: Date de fin pour filtrer (optionnel).

        Returns:
            List[CongeDB]: Liste des congés.
        """
        query = self.db.query(CongeDB).filter(CongeDB.idEmploye == employe_id)
        if start_date:
            query = query.filter(CongeDB.date_debut >= start_date)
        if end_date:
            query = query.filter(CongeDB.date_fin <= end_date)
        conges = query.order_by(CongeDB.date_debut.asc()).all()
        logger.info(f"{len(conges)} congés récupérés pour employé {employe_id}")
        return conges

    def get_conges_by_approbateur(self, approbateur_id: UUID) -> List[CongeDB]:
        """
        Récupère les congés approuvés par un utilisateur.

        Args:
            approbateur_id: ID de l'approbateur.

        Returns:
            List[CongeDB]: Liste des congés approuvés.
        """
        conges = self.db.query(CongeDB).filter(CongeDB.approuve_par == approbateur_id).all()
        logger.info(f"{len(conges)} congés récupérés pour approbateur {approbateur_id}")
        return conges

    def update_conge(self, conge: CongeDB, update_data: Dict, approbateur: Optional[EmployeDB]) -> CongeDB:
        """
        Met à jour un congé existant.

        Args:
            conge: Congé à mettre à jour.
            update_data: Données à mettre à jour.
            approbateur: Employé ayant approuvé le congé (optionnel).

        Returns:
            CongeDB: Congé mis à jour.
        """
        for field, value in update_data.items():
            if hasattr(conge, field):
                setattr(conge, field, value)
        if approbateur:
            conge.approuve_par = approbateur.idEmploye
        conge.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(conge)
        logger.info(f"Congé mis à jour : {conge.idConge}")
        return conge

    def delete_conge(self, conge: CongeDB):
        """
        Supprime un congé.

        Args:
            conge: Congé à supprimer.
        """
        self.db.delete(conge)
        self.db.commit()
        logger.info(f"Congé supprimé : {conge.idConge}")
        
    def get_conges_by_entreprise(self, entreprise_id: UUID) -> List[CongeDB]:
        """
        Récupère tous les congés d'une entreprise donnée.
        """
        conges = (
            self.db.query(CongeDB)
            .join(EmployeDB, EmployeDB.idEmploye == CongeDB.idEmploye)
            .filter(EmployeDB.idEntreprise == entreprise_id)
            .order_by(CongeDB.date_debut.asc())
            .all()
        )
        logger.info(f"{len(conges)} congés récupérés pour entreprise {entreprise_id}")
        return conges
