from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
import traceback

from app.schemas.schemas import LoginCredentials, SendCodeRequest, VerifyCodeRequest, MessageResponse, TokenData
from app.services.auth_service import AuthService
from app.repositories.employe_repository import EmployeRepository
from app.database import get_db

router = APIRouter(
    prefix="",
    tags=["Authentification"],
    responses={
        401: {"description": "Non autorisé (email/mot de passe incorrect ou code invalide)"},
        400: {"description": "Requête invalide ou données incorrectes"},
        500: {"description": "Erreur interne du serveur"},
    }
)

logger = logging.getLogger("auth_controller")

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    employe_repo = EmployeRepository(db)
    return AuthService(employe_repo)

@router.post(
    "/login",
    summary="Connecter un utilisateur et vérifier son rôle",
    response_model=TokenData,
)
async def login_controller(
    credentials: LoginCredentials,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        response = await auth_service.authenticate_user(credentials)
        return response
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception:
        logger.error("Erreur inattendue lors du login:")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur. Veuillez réessayer plus tard."
        )

@router.post(
    "/send-code",
    summary="Envoyer un code de vérification pour la connexion",
    response_model=MessageResponse
)
async def send_login_code_controller(
    request: SendCodeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        response = await auth_service.send_login_code(request)
        return MessageResponse(**response)
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception:
        logger.error("Erreur inattendue lors de l'envoi du code:")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erreur lors de l'envoi du code.")

@router.post(
    "/verify-code",
    summary="Vérifier le code de connexion et connecter l'utilisateur",
    response_model=TokenData
)
async def verify_login_code_controller(
    request: VerifyCodeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        response = await auth_service.verify_login_code(request)
        return response
    except HTTPException as e:
        logger.warning(f"Erreur HTTP: {e.detail}")
        raise e
    except Exception:
        logger.error("Erreur inattendue lors de la vérification du code:")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erreur lors de la vérification du code.")
