# app/api/v1/endpoints/register.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.models import  EmployeDB
from app.services.registration_service import RegistrationService
from app.repositories.employe_repository import EmployeRepository
from app.database import get_db
from app.api.deps import get_current_active_admin
from app.core.security import get_password_hash 
from app.schemas.schemas import PersonalInfo, PersonalInfo, FinalRegistrationData, UserVerification, CompanyInfo, CompanyVerification

router = APIRouter(
    prefix="",
    tags=["Inscription"],
)

def get_registration_service(db: Session = Depends(get_db)) -> RegistrationService:
    return RegistrationService(db)

@router.post("/personal-info", summary="Valider les informations personnelles et envoyer le code")
async def validate_personal_info_controller(
    data: PersonalInfo,
    registration_service: RegistrationService = Depends(get_registration_service)
):
    """Valide les informations personnelles et envoie un code de vérification."""
    try:
        response = await registration_service.process_personal_info(data)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/verify-user-email", summary="Vérifier le code de l'utilisateur")
async def verify_user_email_controller(
    data: UserVerification,
    registration_service: RegistrationService = Depends(get_registration_service)
):
    """Vérifie le code de vérification de l'utilisateur."""
    try:
        response = await registration_service.verify_user_email(data)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/company-info", summary="Valider les informations de l'entreprise")
async def validate_company_info_controller(
    data: CompanyInfo,
    user_email: EmailStr = Query(...),
    registration_service: RegistrationService = Depends(get_registration_service)
):
    """Valide les informations de l'entreprise et envoie un code de vérification."""
    try:
        response = await registration_service.process_company_info(data, user_email)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/verify-company-email", summary="Vérifier le code de l'entreprise")
async def verify_company_email_controller(
    data: CompanyVerification,
    registration_service: RegistrationService = Depends(get_registration_service)
):
    """Vérifie le code de vérification de l'entreprise."""
    try:
        response = await registration_service.verify_company_email(data)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/complete", summary="Finaliser l'inscription")
async def complete_registration_controller(
    data: FinalRegistrationData,
    registration_service: RegistrationService = Depends(get_registration_service)
):
    """
    Finalise l'inscription sans nécessiter d'authentification.
    Un utilisateur système est utilisé si aucun administrateur n'est connecté.
    """
    try:
        response = await registration_service.complete_registration(data)  # <-- ici supprimer le None
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/resume", summary="Reprendre une inscription en attente")
async def resume_pending_registration(
    user_email: EmailStr = Query(...),
    registration_service: RegistrationService = Depends(get_registration_service)
):
    """Récupère l'état d'une inscription en attente."""
    try:
        return registration_service.get_pending_state(user_email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))