from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from app.models import CongeDB, EmployeDB
from app.repositories.conge_repository import CongeRepository
from app.schemas.schemas import CongeCreate, CongeUpdate, CongeResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CongeService:
    def __init__(self, db: Session):
        self.repository = CongeRepository(db)

    def create_conge(self, conge_data: CongeCreate, current_user: EmployeDB) -> CongeResponse:
        """
        Crée un nouveau congé pour un employé.

        Args:
            conge_data: Données du congé.
            current_user: Utilisateur authentifié.

        Returns:
            CongeResponse: Détails du congé créé.

        Raises:
            HTTPException: Si l'utilisateur n'a pas les droits ou si les données sont invalides.
        """
        if current_user.role not in ["admin", "manager", "employee"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à créer un congé.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les admins, managers ou employés peuvent créer un congé."
            )
        employe = self.repository.db.query(EmployeDB).filter(EmployeDB.idEmploye == conge_data.idEmploye).first()
        if not employe:
            logger.error(f"Employé avec ID {conge_data.idEmploye} non trouvé.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé.")
        if current_user.idEntreprise != employe.idEntreprise:
            logger.error(f"Utilisateur {current_user.email} n'appartient pas à l'entreprise de l'employé {conge_data.idEmploye}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à créer un congé pour cet employé."
            )
        conge_dict = conge_data.dict()
        conge = self.repository.create_conge(conge_dict, employe, None)
        logger.info(f"Congé créé pour employé {employe.idEmploye} par {current_user.email}")
        return self._map_conge_to_response(conge)

    def get_conge_by_id(self, conge_id: UUID, current_user: EmployeDB) -> CongeResponse:
        """
        Récupère un congé par son ID.

        Args:
            conge_id: ID du congé.
            current_user: Utilisateur authentifié.

        Returns:
            CongeResponse: Détails du congé.

        Raises:
            HTTPException: Si le congé n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        conge = self.repository.get_conge_by_id(conge_id)
        if not conge:
            logger.error(f"Congé avec ID {conge_id} non trouvé.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Congé non trouvé.")
        if current_user.idEntreprise != conge.employe.idEntreprise:
            logger.error(f"Utilisateur {current_user.email} n'a pas accès au congé {conge_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à accéder à ce congé."
            )
        return self._map_conge_to_response(conge)

    def get_conges_by_employe_id(self, employe_id: UUID, current_user: EmployeDB, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CongeResponse]:
        """
        Récupère les congés d'un employé.

        Args:
            employe_id: ID de l'employé.
            current_user: Utilisateur authentifié.
            start_date: Date de début pour filtrer (optionnel).
            end_date: Date de fin pour filtrer (optionnel).

        Returns:
            List[CongeResponse]: Liste des congés.

        Raises:
            HTTPException: Si l'employé n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        employe = self.repository.db.query(EmployeDB).filter(EmployeDB.idEmploye == employe_id).first()
        if not employe:
            logger.error(f"Employé avec ID {employe_id} non trouvé.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé.")
        if current_user.idEntreprise != employe.idEntreprise:
            logger.error(f"Utilisateur {current_user.email} n'a pas accès à l'employé {employe_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à accéder aux congés de cet employé."
            )
        conges = self.repository.get_conges_by_employe_id(employe_id, start_date, end_date)
        return [self._map_conge_to_response(c) for c in conges]

    def update_conge(self, conge_id: UUID, conge_data: CongeUpdate, current_user: EmployeDB) -> CongeResponse:
        """
        Met à jour un congé existant.

        Args:
            conge_id: ID du congé.
            conge_data: Données à mettre à jour.
            current_user: Utilisateur authentifié.

        Returns:
            CongeResponse: Détails du congé mis à jour.

        Raises:
            HTTPException: Si le congé n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        conge = self.repository.get_conge_by_id(conge_id)
        if not conge:
            logger.error(f"Congé avec ID {conge_id} non trouvé.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Congé non trouvé.")
        if current_user.idEntreprise != conge.employe.idEntreprise:
            logger.error(f"Utilisateur {current_user.email} n'a pas accès au congé {conge_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à modifier ce congé."
            )
        if conge_data.statut and conge_data.statut != "en_attente" and current_user.role not in ["admin", "manager"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à modifier le statut du congé {conge_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les admins ou managers peuvent modifier le statut du congé."
            )
        approbateur = current_user if conge_data.statut in ["approuve", "refuse"] else None
        update_data = conge_data.dict(exclude_unset=True)
        updated_conge = self.repository.update_conge(conge, update_data, approbateur)
        logger.info(f"Congé mis à jour : {conge_id} par {current_user.email}")
        return self._map_conge_to_response(updated_conge)

    def delete_conge(self, conge_id: UUID, current_user: EmployeDB) -> dict:
        """
        Supprime un congé.

        Args:
            conge_id: ID du congé.
            current_user: Utilisateur authentifié.

        Returns:
            dict: Message de confirmation.

        Raises:
            HTTPException: Si le congé n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        conge = self.repository.get_conge_by_id(conge_id)
        if not conge:
            logger.error(f"Congé avec ID {conge_id} non trouvé.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Congé non trouvé.")
        if current_user.idEntreprise != conge.employe.idEntreprise:
            logger.error(f"Utilisateur {current_user.email} n'a pas accès au congé {conge_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à supprimer ce congé."
            )
        self.repository.delete_conge(conge)
        logger.info(f"Congé supprimé : {conge_id} par {current_user.email}")
        return {"message": "Congé supprimé avec succès."}

    def get_conges_by_approbateur(self, approbateur_id: UUID, current_user: EmployeDB) -> List[CongeResponse]:
        """
        Récupère les congés approuvés par un utilisateur.

        Args:
            approbateur_id: ID de l'approbateur.
            current_user: Utilisateur authentifié.

        Returns:
            List[CongeResponse]: Liste des congés approuvés.

        Raises:
            HTTPException: Si l'utilisateur n'a pas les droits.
        """
        if current_user.idEmploye != approbateur_id and current_user.role not in ["admin", "manager"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à accéder aux congés approuvés par {approbateur_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à accéder à ces congés."
            )
        conges = self.repository.get_conges_by_approbateur(approbateur_id)
        return [self._map_conge_to_response(c) for c in conges]

    def _map_conge_to_response(self, conge: CongeDB) -> CongeResponse:
        """
        Mappe un objet CongeDB à un modèle Pydantic CongeResponse.
        """
        return CongeResponse(
            idConge=conge.idConge,
            idEmploye=conge.idEmploye,
            type_conge=conge.type_conge,
            date_debut=conge.date_debut,
            date_fin=conge.date_fin,
            statut=conge.statut,
            commentaire=conge.commentaire,
            approuve_par=conge.approuve_par,
            created_at=conge.created_at,
            updated_at=conge.updated_at
        )
        
    def get_conges_by_entreprise(self, entreprise_id: UUID, current_user: EmployeDB) -> List[CongeResponse]:
        """
        Récupère tous les congés d'une entreprise.
        Seuls admin/manager ou super-admin peuvent accéder.
        """
        if current_user.role not in ["admin", "manager", "super-admin"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à lister les congés de l'entreprise.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les admins, managers ou super-admin peuvent consulter les congés d'une entreprise."
            )

        # Limiter aux congés de sa propre entreprise sauf pour les super-admins
        if current_user.idEntreprise != entreprise_id and current_user.role != "super-admin":
            logger.error(f"Utilisateur {current_user.email} tente d'accéder aux congés d'une autre entreprise.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé pour cette entreprise."
            )

        conges = self.repository.get_conges_by_entreprise(entreprise_id)
        return [self._map_conge_to_response(c) for c in conges]
