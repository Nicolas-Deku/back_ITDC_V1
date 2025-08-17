from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.services.conge_service import CongeService
from app.schemas.schemas import CongeCreate, CongeUpdate, CongeResponse, MessageResponse
from app.api.deps import get_current_active_employe, get_current_active_manager_or_admin
from app.models import EmployeDB
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Congés"])

def get_conge_service(db: Session = Depends(get_db)) -> CongeService:
    return CongeService(db)

@router.post(
    "/",
    response_model=CongeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un congé",
    dependencies=[Depends(get_current_active_employe)]
)
async def create_conge(
    conge_data: CongeCreate,
    current_user: EmployeDB = Depends(get_current_active_employe),
    conge_service: CongeService = Depends(get_conge_service)
):
    """
    Crée un nouveau congé pour un employé.

    Args:
        conge_data: Données du congé.
        current_user: Utilisateur authentifié (tous les rôles).
        conge_service: Service pour gérer les congés.

    Returns:
        CongeResponse: Détails du congé créé.
    """
    try:
        conge = conge_service.create_conge(conge_data, current_user)
        logger.info(f"Congé créé pour employé {conge_data.idEmploye} par {current_user.email}")
        return conge
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la création du congé: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la création du congé: {e}")

@router.get(
    "/{conge_id}",
    response_model=CongeResponse,
    summary="Récupérer un congé par ID",
    dependencies=[Depends(get_current_active_employe)]
)
async def get_conge(
    conge_id: UUID,
    current_user: EmployeDB = Depends(get_current_active_employe),
    conge_service: CongeService = Depends(get_conge_service)
):
    """
    Récupère les détails d'un congé spécifique.

    Args:
        conge_id: ID du congé.
        current_user: Utilisateur authentifié (tous les rôles).
        conge_service: Service pour gérer les congés.

    Returns:
        CongeResponse: Détails du congé.
    """
    try:
        conge = conge_service.get_conge_by_id(conge_id, current_user)
        return conge
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération du congé: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération du congé: {e}")

@router.get(
    "/employe/{employe_id}",
    response_model=List[CongeResponse],
    summary="Lister les congés d'un employé",
    dependencies=[Depends(get_current_active_employe)]
)
async def get_conges_by_employe(
    employe_id: UUID,
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: EmployeDB = Depends(get_current_active_employe),
    conge_service: CongeService = Depends(get_conge_service)
):
    """
    Liste les congés d'un employé, avec un filtre optionnel sur les dates.

    Args:
        employe_id: ID de l'employé.
        start_date: Date de début pour filtrer (optionnel).
        end_date: Date de fin pour filtrer (optionnel).
        current_user: Utilisateur authentifié (tous les rôles).
        conge_service: Service pour gérer les congés.

    Returns:
        List[CongeResponse]: Liste des congés.
    """
    try:
        conges = conge_service.get_conges_by_employe_id(employe_id, current_user, start_date, end_date)
        return conges
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération des congés: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération des congés: {e}")

@router.put(
    "/{conge_id}",
    response_model=CongeResponse,
    summary="Mettre à jour un congé",
    dependencies=[Depends(get_current_active_employe)]
)
async def update_conge(
    conge_id: UUID,
    conge_data: CongeUpdate,
    current_user: EmployeDB = Depends(get_current_active_employe),
    conge_service: CongeService = Depends(get_conge_service)
):
    """
    Met à jour un congé existant.

    Args:
        conge_id: ID du congé.
        conge_data: Données à mettre à jour.
        current_user: Utilisateur authentifié (tous les rôles).
        conge_service: Service pour gérer les congés.

    Returns:
        CongeResponse: Détails du congé mis à jour.
    """
    try:
        conge = conge_service.update_conge(conge_id, conge_data, current_user)
        logger.info(f"Congé {conge_id} mis à jour par {current_user.email}")
        return conge
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la mise à jour du congé: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la mise à jour du congé: {e}")

@router.delete(
    "/{conge_id}",
    response_model=MessageResponse,
    summary="Supprimer un congé",
    dependencies=[Depends(get_current_active_employe)]
)
async def delete_conge(
    conge_id: UUID,
    current_user: EmployeDB = Depends(get_current_active_employe),
    conge_service: CongeService = Depends(get_conge_service)
):
    """
    Supprime un congé.

    Args:
        conge_id: ID du congé.
        current_user: Utilisateur authentifié (tous les rôles).
        conge_service: Service pour gérer les congés.

    Returns:
        MessageResponse: Message de confirmation.
    """
    try:
        response = conge_service.delete_conge(conge_id, current_user)
        logger.info(f"Congé {conge_id} supprimé par {current_user.email}")
        return response
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la suppression du congé: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la suppression du congé: {e}")

@router.get(
    "/approbateur/{approbateur_id}",
    response_model=List[CongeResponse],
    summary="Lister les congés approuvés par un utilisateur",
    dependencies=[Depends(get_current_active_manager_or_admin)]
)
async def get_conges_by_approbateur(
    approbateur_id: UUID,
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin),
    conge_service: CongeService = Depends(get_conge_service)
):
    """
    Liste les congés approuvés par un utilisateur.

    Args:
        approbateur_id: ID de l'approbateur.
        current_user: Utilisateur authentifié (manager/admin).
        conge_service: Service pour gérer les congés.

    Returns:
        List[CongeResponse]: Liste des congés approuvés.
    """
    try:
        conges = conge_service.get_conges_by_approbateur(approbateur_id, current_user)
        return conges
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération des congés approuvés: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération des congés approuvés: {e}")
    
@router.get("/entreprise/{entreprise_id}", response_model=List[CongeResponse])
async def get_conges_by_entreprise(
    entreprise_id: UUID,
    service: CongeService = Depends(get_conge_service),
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin),
):
    return service.get_conges_by_entreprise(entreprise_id, current_user)