from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.services.session_service import SessionService
from app.schemas.schemas import SessionResponse, MessageResponse
from app.api.deps import get_current_active_employe, get_current_active_manager_or_admin
from app.models import EmployeDB
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Sessions"])

def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    return SessionService(db)

@router.post(
    "/",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une session",
    dependencies=[Depends(get_current_active_employe)]
)
async def create_session(
    current_user: EmployeDB = Depends(get_current_active_employe),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Crée une nouvelle session pour l'utilisateur authentifié.

    Args:
        current_user: Utilisateur authentifié (tous les rôles).
        session_service: Service pour gérer les sessions.

    Returns:
        SessionResponse: Détails de la session créée.
    """
    try:
        session = session_service.create_session(current_user)
        logger.info(f"Session créée pour employé {current_user.email}")
        return session
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la création de la session: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la création de la session: {e}")

@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Récupérer une session par ID",
    dependencies=[Depends(get_current_active_employe)]
)
async def get_session(
    session_id: UUID,
    current_user: EmployeDB = Depends(get_current_active_employe),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Récupère les détails d'une session spécifique.

    Args:
        session_id: ID de la session.
        current_user: Utilisateur authentifié (tous les rôles).
        session_service: Service pour gérer les sessions.

    Returns:
        SessionResponse: Détails de la session.
    """
    try:
        session = session_service.get_session_by_id(session_id, current_user)
        return session
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération de la session: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération de la session: {e}")

@router.get(
    "/employe/{employe_id}",
    response_model=List[SessionResponse],
    summary="Lister les sessions d'un employé",
    dependencies=[Depends(get_current_active_employe)]
)
async def get_sessions_by_employe(
    employe_id: UUID,
    current_user: EmployeDB = Depends(get_current_active_employe),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Liste toutes les sessions actives d'un employé.

    Args:
        employe_id: ID de l'employé.
        current_user: Utilisateur authentifié (tous les rôles).
        session_service: Service pour gérer les sessions.

    Returns:
        List[SessionResponse]: Liste des sessions actives.
    """
    try:
        sessions = session_service.get_sessions_by_employe_id(employe_id, current_user)
        return sessions
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération des sessions: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la récupération des sessions: {e}")

@router.delete(
    "/{session_id}",
    response_model=MessageResponse,
    summary="Révoquer une session",
    dependencies=[Depends(get_current_active_employe)]
)
async def revoke_session(
    session_id: UUID,
    current_user: EmployeDB = Depends(get_current_active_employe),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Révoque une session spécifique.

    Args:
        session_id: ID de la session.
        current_user: Utilisateur authentifié (tous les rôles).
        session_service: Service pour gérer les sessions.

    Returns:
        MessageResponse: Message de confirmation.
    """
    try:
        response = session_service.revoke_session(session_id, current_user)
        logger.info(f"Session {session_id} révoquée par {current_user.email}")
        return response
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la révocation de la session: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la révocation de la session: {e}")

@router.delete(
    "/cleanup",
    response_model=MessageResponse,
    summary="Nettoyer les sessions expirées",
    dependencies=[Depends(get_current_active_manager_or_admin)]
)
async def cleanup_sessions(
    session_service: SessionService = Depends(get_session_service)
):
    """
    Supprime toutes les sessions expirées.

    Args:
        session_service: Service pour gérer les sessions.

    Returns:
        MessageResponse: Message de confirmation.
    """
    try:
        response = session_service.cleanup_expired_sessions()
        logger.info("Sessions expirées nettoyées")
        return response
    except Exception as e:
        logger.error(f"Erreur inattendue lors du nettoyage des sessions: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors du nettoyage des sessions: {e}")