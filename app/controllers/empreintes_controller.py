from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database import get_db
from app.services.employe_service import EmployeService
from app.schemas.schemas import (
    EmpreinteCreate,
    EmpreinteResponse,
    FingerprintScanRequest,
    MessageResponse
)
from app.api.deps import (
    get_current_active_employe,
    get_current_active_manager_or_admin,
    get_employe_service
)
from app.models import EmployeDB
import logging

# Configurer la journalisation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/empreintes", tags=["Empreintes"])

@router.post(
    "/",
    response_model=EmpreinteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter une empreinte digitale pour un employé",
    dependencies=[Depends(get_current_active_manager_or_admin)]
)
def add_empreinte_endpoint(
    id_employe: uuid.UUID,
    empreinte_data: EmpreinteCreate,
    employe_service: EmployeService = Depends(get_employe_service),
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin)
):
    """
    Ajoute une nouvelle empreinte digitale pour un employé spécifié.
    Seuls les admins ou managers peuvent ajouter une empreinte.
    """
    try:
        empreinte = employe_service.add_empreinte(id_employe, empreinte_data)
        logger.info(f"Empreinte ajoutée pour employé {id_employe} par {current_user.email}")
        return empreinte
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de l'ajout de l'empreinte: {e}")

@router.get(
    "/{id_employe}",
    response_model=List[EmpreinteResponse],
    summary="Récupérer toutes les empreintes digitales d'un employé",
    dependencies=[Depends(get_current_active_employe)]
)
def get_empreintes_endpoint(
    id_employe: uuid.UUID,
    current_user: EmployeDB = Depends(get_current_active_employe),
    employe_service: EmployeService = Depends(get_employe_service)
):
    """
    Récupère toutes les empreintes digitales d'un employé donné.
    Un employé peut voir ses propres empreintes, les admins/managers peuvent voir celles de tous.
    """
    if str(current_user.idEmploye) != str(id_employe) and current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'êtes pas autorisé à voir ces empreintes.")
    
    try:
        empreintes = employe_service.get_employe_empreintes(id_employe)
        return empreintes
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération des empreintes: {e}")

@router.delete(
    "/{id_empreinte}",
    response_model=MessageResponse,
    summary="Supprimer une empreinte digitale",
    dependencies=[Depends(get_current_active_manager_or_admin)]
)
def delete_empreinte_endpoint(
    id_empreinte: uuid.UUID,
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin),
    employe_service: EmployeService = Depends(get_employe_service)
):
    """
    Supprime une empreinte digitale spécifique.
    Seuls les admins ou managers peuvent supprimer une empreinte.
    """
    try:
        response = employe_service.delete_empreinte(id_empreinte)
        logger.info(f"Empreinte {id_empreinte} supprimée par {current_user.email}")
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la suppression de l'empreinte: {e}")

@router.post(
    "/validate-fingerprint",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Valider l'empreinte digitale d'un employé nouvellement enregistré"
)
def validate_fingerprint_endpoint(
    scan_request: FingerprintScanRequest,
    employe_service: EmployeService = Depends(get_employe_service)
):
    """
    Valide l'empreinte digitale d'un employé après son enregistrement.
    Enregistre l'empreinte dans la base de données et met à jour l'état de l'inscription.
    """
    try:
        employe = employe_service.employe_repo.get_employe_by_id(scan_request.idEmploye)
        if not employe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")

        # Vérifier si une inscription en attente existe
        pending = employe_service.employe_repo.get_pending_registration(employe.email)
        if not pending or pending.get("personal_info", {}).get("status") != "pending_fingerprint_validation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucune validation d'empreinte digitale en attente pour cet employé."
            )

        # Enregistrer l'empreinte digitale
        empreinte_data = EmpreinteCreate(donneesBiometriques=scan_request.donneesBiometriques)
        employe_service.add_empreinte(employe.idEmploye, empreinte_data)

        # Supprimer l'inscription en attente après validation réussie
        employe_service.employe_repo.delete_pending_registration(employe.email)
        logger.info(f"Empreinte digitale validée et enregistrée pour {employe.email}")

        return MessageResponse(message="Empreinte digitale validée avec succès. Inscription finalisée.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la validation de l'empreinte: {e}")