from fastapi import APIRouter, Depends, status
from typing import List
from uuid import UUID

from app.schemas.schemas import PosteCreate, PosteUpdate, PosteResponse
from app.models import EmployeDB
from app.database import get_db  # à adapter selon ton projet
from sqlalchemy.orm import Session
from app.services.poste_service import PosteService
from app.api.deps import get_current_active_admin

router = APIRouter(prefix="", tags=["Postes"])


@router.post("/", response_model=PosteResponse, status_code=status.HTTP_201_CREATED)
def create_poste(
    poste_data: PosteCreate,
    db: Session = Depends(get_db),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    service = PosteService(db)
    return service.create_poste(poste_data, current_user)


@router.get("/{poste_id}", response_model=PosteResponse)
def get_poste(
    poste_id: UUID,
    db: Session = Depends(get_db),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    service = PosteService(db)
    return service.get_poste(poste_id, current_user)


@router.get("/entreprises/{idEntreprise}", response_model=List[PosteResponse])
def get_postes_by_entreprise(
    idEntreprise: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    service = PosteService(db)
    return service.list_postes(idEntreprise, current_user, skip, limit)


@router.put("/{poste_id}", response_model=PosteResponse)
def update_poste(
    poste_id: UUID,
    update_data: PosteUpdate,
    db: Session = Depends(get_db),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    service = PosteService(db)
    return service.update_poste(poste_id, update_data, current_user)


@router.delete("/{poste_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_poste(
    poste_id: UUID,
    db: Session = Depends(get_db),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    service = PosteService(db)
    service.delete_poste(poste_id, current_user)
    return {"detail": "Poste supprimé"}
