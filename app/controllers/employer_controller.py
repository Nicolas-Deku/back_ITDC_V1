from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
import logging
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from fastapi.responses import JSONResponse

from app.database import get_db
from app.services.employe_service import EmployeService
from app.services.empreinte_service import EmpreinteService
from app.services.registration_service import RegistrationService
from app.schemas.schemas import (
    EmployeCreate,
    EmployeUpdate,
    EmployeResponse,
    EmpreinteCreate,
    EmpreinteResponse,
    FingerprintScanRequest,
    PresenceResponse,
    MessageResponse,
    Notification,
)
from app.api.deps import (
    get_current_active_manager_or_admin,
    get_current_active_employe,
    get_employe_service
)
from app.models import EmployeDB

# Configurer la journalisation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Employés"])

def get_empreinte_service(db: Session = Depends(get_db)) -> EmpreinteService:
    return EmpreinteService(db)

def get_registration_service(db: Session = Depends(get_db)) -> RegistrationService:
    return RegistrationService(db)

@router.post(
    "/",
    response_model=EmployeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouvel employé",
    dependencies=[Depends(get_current_active_manager_or_admin)]
)
async def create_employe_endpoint(
    employe: EmployeCreate,
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin),
    employe_service: EmployeService = Depends(get_employe_service)
):
    """
    Crée un nouvel employé.
    """
    try:
        return await employe_service.create_employe(employe, current_user)
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la création de l'employé: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de l'employé: {e}"
        )

@router.get(
    "/liste",
    response_model=List[EmployeResponse],
    summary="Lister tous les employés",
    dependencies=[Depends(get_current_active_manager_or_admin)]
)
def list_employes_endpoint(
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin),
    employe_service: EmployeService = Depends(get_employe_service)
):
    """
    Liste tous les employés.
    """
    try:
        return employe_service.list_employes(current_user)
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération des employés: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération des employés: {e}")

@router.get(
    "/{idEmploye}",
    response_model=EmployeResponse,
    summary="Obtenir un employé par ID",
    dependencies=[Depends(get_current_active_employe)]
)
def get_employe_by_id_endpoint(
    idEmploye: UUID,
    current_user: EmployeDB = Depends(get_current_active_employe),
    employe_service: EmployeService = Depends(get_employe_service)
):
    """
    Récupère un employé par son ID.
    """
    try:
        employe = employe_service.get_employe_by_id(idEmploye)
        if not employe:
            logger.warning(f"Employé avec ID {idEmploye} non trouvé.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")
        if str(current_user.idEmploye) != str(idEmploye) and current_user.role not in ["admin", "manager"]:
            logger.warning(f"Utilisateur {current_user.email} non autorisé à voir le profil de {idEmploye}.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'êtes pas autorisé à voir ce profil.")
        return employe
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération de l'employé: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération de l'employé: {e}")

@router.put(
    "/{idEmploye}",
    response_model=EmployeResponse,
    summary="Mettre à jour un employé",
    dependencies=[Depends(get_current_active_manager_or_admin)]
)
def update_employe_endpoint(
    idEmploye: UUID,
    update_data: EmployeUpdate,
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin),
    employe_service: EmployeService = Depends(get_employe_service)
):
    """
    Met à jour un employé existant.
    """
    try:
        updated_employe = employe_service.update_employe(idEmploye, update_data, current_user)
        logger.info(f"Employé {idEmploye} mis à jour par {current_user.email}")
        return updated_employe
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la mise à jour de l'employé: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la mise à jour de l'employé: {e}")

@router.delete(
    "/{idEmploye}",
    response_model=MessageResponse,
    summary="Supprimer un employé",
    dependencies=[Depends(get_current_active_manager_or_admin)]
)
async def delete_employe_endpoint(
    idEmploye: UUID,
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin),
    employe_service: EmployeService = Depends(get_employe_service)
):
    """
    Supprime un employé.
    """
    try:
        response = await employe_service.delete_employe(idEmploye, current_user)
        logger.info(f"Employé {idEmploye} supprimé par {current_user.email}")
        return response
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la suppression de l'employé: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la suppression de l'employé: {e}")


@router.post(
    "/{idEmploye}/empreintes",
    response_model=EmpreinteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter une empreinte digitale pour un employé",
    dependencies=[Depends(get_current_active_manager_or_admin)]
)
def add_empreinte_endpoint(
    idEmploye: UUID,
    empreinte_data: EmpreinteCreate,
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin),
    empreinte_service: EmpreinteService = Depends(get_empreinte_service)
):
    """
    Ajoute une nouvelle empreinte digitale pour un employé spécifié.
    Seuls les admins ou managers peuvent ajouter une empreinte.
    """
    try:
        empreinte = empreinte_service.add_empreinte(idEmploye, empreinte_data, current_user)
        logger.info(f"Empreinte ajoutée pour employé {idEmploye} par {current_user.email}")
        return empreinte
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'ajout de l'empreinte: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de l'ajout de l'empreinte: {e}")

@router.get(
    "/{idEmploye}/empreintes",
    response_model=List[EmpreinteResponse],
    summary="Récupérer toutes les empreintes digitales d'un employé",
    dependencies=[Depends(get_current_active_employe)]
)
def get_empreintes_endpoint(
    idEmploye: UUID,
    current_user: EmployeDB = Depends(get_current_active_employe),
    empreinte_service: EmpreinteService = Depends(get_empreinte_service)
):
    """
    Récupère toutes les empreintes digitales d'un employé donné.
    Un employé peut voir ses propres empreintes, les admins/managers peuvent voir celles de tous.
    """
    try:
        empreintes = empreinte_service.get_employe_empreintes(idEmploye, current_user)
        logger.info(f"{len(empreintes)} empreintes récupérées pour employé {idEmploye} par {current_user.email}")
        return empreintes
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération des empreintes: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération des empreintes: {e}")

@router.delete(
    "/{idEmploye}/empreintes/{idEmpreinte}",
    response_model=MessageResponse,
    summary="Supprimer une empreinte digitale",
    dependencies=[Depends(get_current_active_manager_or_admin)]
)
def delete_empreinte_endpoint(
    idEmploye: UUID,
    idEmpreinte: UUID,
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin),
    empreinte_service: EmpreinteService = Depends(get_empreinte_service)
):
    """
    Supprime une empreinte digitale spécifique.
    Seuls les admins ou managers peuvent supprimer une empreinte.
    """
    try:
        response = empreinte_service.delete_empreinte(idEmpreinte, current_user)
        logger.info(f"Empreinte {idEmpreinte} supprimée pour employé {idEmploye} par {current_user.email}")
        return response
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la suppression de l'empreinte: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la suppression de l'empreinte: {e}")

@router.post(
    "/validate-fingerprint",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Valider l'empreinte digitale d'un employé nouvellement enregistré"
)
def validate_fingerprint_endpoint(
    scan_request: FingerprintScanRequest,
    empreinte_service: EmpreinteService = Depends(get_empreinte_service),
    registration_service: RegistrationService = Depends(get_registration_service)
):
    """
    Valide l'empreinte digitale d'un employé après son enregistrement.
    Enregistre l'empreinte dans la base de données et finalise l'inscription.
    """
    try:
        # Valider l'empreinte
        empreinte_response = empreinte_service.validate_fingerprint(scan_request)
        
        # Finaliser l'inscription en supprimant PendingRegistration
        employe = empreinte_service.employe_repo.get_employe_by_id(scan_request.idEmploye)
        if not employe:
            logger.error(f"Employé avec ID {scan_request.idEmploye} non trouvé.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")
        
        registration_service.complete_fingerprint_validation(employe.email)
        logger.info(f"Inscription finalisée pour {employe.email} après validation de l'empreinte")
        
        return MessageResponse(message="Empreinte digitale validée et inscription finalisée avec succès.")
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la validation de l'empreinte: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la validation de l'empreinte: {e}")


@router.post(
    "/scan-fingerprint",
    response_model=PresenceResponse,
    summary="Scanner une empreinte pour enregistrer la présence"
)
def scan_fingerprint_endpoint(
    scan_data: FingerprintScanRequest,
    employe_service: EmployeService = Depends(get_employe_service)
):
    """
    Enregistre une présence (CHECK_IN ou CHECK_OUT) en validant l'empreinte digitale.
    """
    try:
        presence = employe_service.scan_fingerprint(scan_data)
        logger.info(f"Présence enregistrée pour employé {scan_data.idEmploye}")
        return presence
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors du scan de l'empreinte: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors du scan de l'empreinte: {e}")
    
@router.get(
    "/entreprise/{idEntreprise}/employes",
    response_model=List[EmployeResponse],
    summary="Lister les employés d'une entreprise",
    dependencies=[Depends(get_current_active_manager_or_admin)]
)
def list_employes_by_entreprise_endpoint(
    idEntreprise: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin),
    employe_service: EmployeService = Depends(get_employe_service)
):
    try:
        return employe_service.list_employes_by_entreprise(idEntreprise, current_user, skip, limit)
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération des employés par entreprise: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération des employés: {e}")
