from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decode_access_token
from app.schemas.schemas import TokenData
from app.repositories.employe_repository import EmployeRepository
from app.models import EmployeDB
from app.services.employe_service import EmployeService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> EmployeDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    try:
        token_data = TokenData(**payload)
    except Exception:
        raise credentials_exception

    employe_repo = EmployeRepository(db)
    user = employe_repo.get_employe_by_email(token_data.email)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_admin(current_user: EmployeDB = Depends(get_current_user)):
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas les privilèges suffisants."
        )
    return current_user

def get_current_active_manager_or_admin(current_user: EmployeDB = Depends(get_current_user)):
    if current_user.role.lower() not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas les privilèges suffisants."
        )
    return current_user

def get_current_active_employe(current_user: EmployeDB = Depends(get_current_user)):
    if current_user.role.lower() not in ["admin", "manager", "employee"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à accéder à cette ressource."
        )
    return current_user

# Ajout de la fonction manquante
def get_employe_service(db: Session = Depends(get_db)) -> EmployeService:
    return EmployeService(db)
