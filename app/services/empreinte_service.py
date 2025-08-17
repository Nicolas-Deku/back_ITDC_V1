from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from app.repositories.empreinte_repository import EmpreinteRepository
from app.repositories.employe_repository import EmployeRepository
from app.schemas.schemas import EmpreinteCreate, EmpreinteResponse, FingerprintScanRequest, MessageResponse
from app.models import EmployeDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmpreinteService:
    def __init__(self, db: Session):
        self.db = db
        self.empreinte_repo = EmpreinteRepository(db)
        self.employe_repo = EmployeRepository(db)

    def add_empreinte(self, id_employe: UUID, empreinte_data: EmpreinteCreate, current_user: EmployeDB) -> EmpreinteResponse:
        """
        Ajoute une nouvelle empreinte digitale pour un employé spécifié.
        Seuls les admins ou managers peuvent ajouter une empreinte.
        """
        employe = self.employe_repo.get_employe_by_id(id_employe)
        if not employe:
            logger.error(f"Employé avec ID {id_employe} non trouvé.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")
        if current_user.role not in ["admin", "manager"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à ajouter une empreinte.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les admins ou managers peuvent ajouter une empreinte."
            )
        new_empreinte = self.empreinte_repo.create_empreinte(id_employe, empreinte_data.donneesBiometriques)
        logger.info(f"Empreinte ajoutée pour employé {id_employe} par {current_user.email}")
        return EmpreinteResponse.model_validate(new_empreinte)

    def get_employe_empreintes(self, id_employe: UUID, current_user: EmployeDB) -> List[EmpreinteResponse]:
        """
        Récupère toutes les empreintes digitales d’un employé.
        Un employé peut voir ses propres empreintes, les admins/managers peuvent voir celles de tous.
        """
        employe = self.employe_repo.get_employe_by_id(id_employe)
        if not employe:
            logger.error(f"Employé avec ID {id_employe} non trouvé.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")
        if str(current_user.idEmploye) != str(id_employe) and current_user.role not in ["admin", "manager"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à voir les empreintes de {id_employe}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à voir ces empreintes."
            )
        empreintes = self.empreinte_repo.get_empreintes_by_employe_id(id_employe)
        logger.info(f"{len(empreintes)} empreintes récupérées pour employé {id_employe} par {current_user.email}")
        return [EmpreinteResponse.model_validate(emp) for emp in empreintes]

    def delete_empreinte(self, id_empreinte: UUID, current_user: EmployeDB) -> MessageResponse:
        """
        Supprime une empreinte digitale spécifique.
        Seuls les admins ou managers peuvent supprimer une empreinte.
        """
        empreinte = self.empreinte_repo.get_empreinte_by_id(id_empreinte)
        if not empreinte:
            logger.error(f"Empreinte avec ID {id_empreinte} non trouvée.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empreinte non trouvée")
        if current_user.role not in ["admin", "manager"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à supprimer l'empreinte {id_empreinte}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les admins ou managers peuvent supprimer une empreinte."
            )
        self.empreinte_repo.delete_empreinte(id_empreinte)
        logger.info(f"Empreinte {id_empreinte} supprimée par {current_user.email}")
        return MessageResponse(message="Empreinte digitale supprimée avec succès")

    def validate_fingerprint(self, scan_request: FingerprintScanRequest) -> MessageResponse:
        """
        Valide une empreinte digitale pour finaliser l’inscription d’un employé.
        """
        employe = self.employe_repo.get_employe_by_id(scan_request.idEmploye)
        if not employe:
            logger.error(f"Employé avec ID {scan_request.idEmploye} non trouvé.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")
        
        # Vérifier si une inscription en attente existe
        pending = self.employe_repo.get_pending_registration(employe.email)
        if not pending or pending.get("personal_info", {}).get("status") != "pending_fingerprint_validation":
            logger.error(f"Aucune validation d'empreinte en attente pour {employe.email}.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucune validation d'empreinte digitale en attente pour cet employé."
            )

        # Enregistrer l'empreinte digitale
        empreinte_data = EmpreinteCreate(donneesBiometriques=scan_request.donneesBiometriques)
        new_empreinte = self.empreinte_repo.create_empreinte(employe.idEmploye, empreinte_data.donneesBiometriques)
        logger.info(f"Empreinte digitale enregistrée pour {employe.email}")
        
        # Note : La suppression de l'inscription en attente est gérée par RegistrationService (ou autre)
        
        return MessageResponse(message="Empreinte digitale validée avec succès.")
