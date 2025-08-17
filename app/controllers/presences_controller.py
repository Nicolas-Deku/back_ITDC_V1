from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.services.presence_service import PresenceService
from app.schemas.schemas import PresenceCreate, PresenceResponse
from app.api.deps import get_current_active_employe, get_current_active_manager_or_admin
from app.models import EmployeDB
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/presences", tags=["Présences"])

def get_presence_service(db: Session = Depends(get_db)) -> PresenceService:
    return PresenceService(db)

@router.post("/", response_model=PresenceResponse, status_code=status.HTTP_201_CREATED)
def create_presence(
    presence: PresenceCreate,
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin),
    presence_service: PresenceService = Depends(get_presence_service)
):
    """
    Crée un nouvel enregistrement de présence.

    Args:
        presence: Données de la présence.
        current_user: Utilisateur authentifié (manager/admin).
        presence_service: Service pour gérer les présences.
    """
    try:
        presence = presence_service.create_presence(presence, current_user)
        logger.info(f"Présence créée pour employé {presence.idEmploye} par {current_user.email}")
        return presence
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la création de la présence: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la création de la présence: {e}")

@router.get("/", response_model=List[PresenceResponse])
def read_presences(
    skip: int = 0,
    limit: int = 100,
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin),
    presence_service: PresenceService = Depends(get_presence_service)
):
    """
    Récupère une liste de présences avec pagination.

    Args:
        skip: Nombre d'éléments à ignorer.
        limit: Nombre maximal d'éléments à retourner.
        current_user: Utilisateur authentifié (manager/admin).
        presence_service: Service pour gérer les présences.
    """
    try:
        presences = presence_service.list_presences(current_user, skip, limit)
        return presences
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération des présences: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération des présences: {e}")

@router.get("/{presence_id}", response_model=PresenceResponse)
def read_presence(
    presence_id: UUID,
    current_user: EmployeDB = Depends(get_current_active_employe),
    presence_service: PresenceService = Depends(get_presence_service)
):
    """
    Récupère une présence par son ID.

    Args:
        presence_id: ID de la présence.
        current_user: Utilisateur authentifié (tous les rôles).
        presence_service: Service pour gérer les présences.
    """
    try:
        presence = presence_service.get_presence(presence_id, current_user)
        return presence
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération de la présence: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération de la présence: {e}")

@router.delete("/{presence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_presence(
    presence_id: UUID,
    current_user: EmployeDB = Depends(get_current_active_employe),
    presence_service: PresenceService = Depends(get_presence_service)
):
    """
    Supprime une présence.

    Args:
        presence_id: ID de la présence.
        current_user: Utilisateur authentifié (admin).
        presence_service: Service pour gérer les présences.
    """
    try:
        presence_service.delete_presence(presence_id, current_user)
        logger.info(f"Présence {presence_id} supprimée par {current_user.email}")
        return {}
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la suppression de la présence: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la suppression de la présence: {e}")