from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime
import logging

from app.database import get_db
from app.services.entreprise_service import EntrepriseService
from app.schemas.schemas import EntrepriseCreate, EntrepriseUpdate, EntrepriseResponse
from app.api.deps import get_current_active_admin
from app.models import EmployeDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/entreprises", tags=["Entreprises"])

def get_entreprise_service(db: Session = Depends(get_db)) -> EntrepriseService:
    return EntrepriseService(db)

@router.post("/", response_model=EntrepriseResponse, status_code=status.HTTP_201_CREATED)
def create_entreprise(
    entreprise: EntrepriseCreate,
    current_user: EmployeDB = Depends(get_current_active_admin),
    entreprise_service: EntrepriseService = Depends(get_entreprise_service)
):
    """
    Crée une nouvelle entreprise.
    """
    try:
        return entreprise_service.create_entreprise(entreprise, current_user)
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la création de l'entreprise: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la création de l'entreprise: {e}")

@router.get("/", response_model=List[EntrepriseResponse])
def read_entreprises(
    skip: int = 0,
    limit: int = 100,
    current_user: EmployeDB = Depends(get_current_active_admin),
    entreprise_service: EntrepriseService = Depends(get_entreprise_service)
):
    """
    Récupère une liste d'entreprises avec pagination.
    """
    try:
        return entreprise_service.list_entreprises(current_user, skip, limit)
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération des entreprises: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération des entreprises: {e}")

@router.get("/{entreprise_id}", response_model=EntrepriseResponse)
def read_entreprise(
    entreprise_id: UUID,
    current_user: EmployeDB = Depends(get_current_active_admin),
    entreprise_service: EntrepriseService = Depends(get_entreprise_service)
):
    """
    Récupère une entreprise par son ID.
    """
    try:
        return entreprise_service.get_entreprise(entreprise_id, current_user)
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération de l'entreprise: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération de l'entreprise: {e}")

@router.put("/{entreprise_id}", response_model=EntrepriseResponse)
def update_entreprise(
    entreprise_id: UUID,
    entreprise_update: EntrepriseUpdate,
    current_user: EmployeDB = Depends(get_current_active_admin),
    entreprise_service: EntrepriseService = Depends(get_entreprise_service)
):
    """
    Met à jour une entreprise existante.
    """
    try:
        return entreprise_service.update_entreprise(entreprise_id, entreprise_update, current_user)
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la mise à jour de l'entreprise: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la mise à jour de l'entreprise: {e}")

@router.delete("/{entreprise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entreprise(
    entreprise_id: UUID,
    current_user: EmployeDB = Depends(get_current_active_admin),
    entreprise_service: EntrepriseService = Depends(get_entreprise_service)
):
    """
    Supprime une entreprise.
    """
    try:
        entreprise_service.delete_entreprise(entreprise_id, current_user)
        return {}
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la suppression de l'entreprise: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la suppression de l'entreprise: {e}")