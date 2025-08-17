from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.services.groupe_service import GroupeService
from app.schemas.schemas import (
    GroupeCreate, GroupeUpdate, GroupeResponse,
    ConfigurationHoraireCreate, ConfigurationHoraireUpdate, ConfigurationHoraireResponse
)
from app.models import EmployeDB
from app.api.deps import get_current_active_admin

router = APIRouter(
    prefix="",
    tags=["Groupes"],
)

def get_groupe_service(db: Session = Depends(get_db)) -> GroupeService:
    return GroupeService(db)

@router.get("/Liste", summary="Lister tous les groupes", response_model=List[GroupeResponse])
async def list_groupes(
    skip: int = 0,
    limit: int = 100,
    groupe_service: GroupeService = Depends(get_groupe_service),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    """
    Liste tous les groupes, avec pagination.
    """
    groupes = groupe_service.get_all_groupes(skip=skip, limit=limit, current_user=current_user)
    return groupes

@router.post("/", summary="Créer un groupe", response_model=GroupeResponse)
async def create_groupe(
    groupe_data: GroupeCreate,
    entreprise_id: UUID,
    groupe_service: GroupeService = Depends(get_groupe_service),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    try:
        groupe = groupe_service.create_groupe(groupe_data, entreprise_id, current_user)
        return groupe
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{groupe_id}", summary="Récupérer un groupe", response_model=GroupeResponse)
async def get_groupe(
    groupe_id: UUID,
    groupe_service: GroupeService = Depends(get_groupe_service),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    groupe = groupe_service.get_groupe_by_id(groupe_id, current_user)
    if not groupe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe non trouvé.")
    return groupe

@router.get("/entreprise/{entreprise_id}", summary="Lister les groupes d'une entreprise", response_model=List[GroupeResponse])
async def get_groupes_by_entreprise(
    entreprise_id: UUID,
    groupe_service: GroupeService = Depends(get_groupe_service),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    groupes = groupe_service.get_groupes_by_entreprise(entreprise_id, current_user)
    return groupes

@router.put("/{groupe_id}", summary="Mettre à jour un groupe", response_model=GroupeResponse)
async def update_groupe(
    groupe_id: UUID,
    groupe_data: GroupeUpdate,
    groupe_service: GroupeService = Depends(get_groupe_service),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    try:
        groupe = groupe_service.update_groupe(groupe_id, groupe_data, current_user)
        return groupe
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{groupe_id}", summary="Supprimer un groupe")
async def delete_groupe(
    groupe_id: UUID,
    groupe_service: GroupeService = Depends(get_groupe_service),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    try:
        groupe_service.delete_groupe(groupe_id, current_user)
        return {"message": "Groupe supprimé avec succès."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{groupe_id}/configuration-horaire", summary="Créer une configuration horaire", response_model=ConfigurationHoraireResponse)
async def create_configuration_horaire(
    groupe_id: UUID,
    config_data: ConfigurationHoraireCreate,
    groupe_service: GroupeService = Depends(get_groupe_service),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    try:
        config = groupe_service.create_configuration_horaire(groupe_id, config_data, current_user)
        return config
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{groupe_id}/configuration-horaire", summary="Récupérer la configuration horaire", response_model=ConfigurationHoraireResponse)
async def get_configuration_horaire(
    groupe_id: UUID,
    groupe_service: GroupeService = Depends(get_groupe_service),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    config = groupe_service.get_configuration_horaire_by_groupe(groupe_id, current_user)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration horaire non trouvée.")
    return config

@router.put("/{groupe_id}/configuration-horaire", summary="Mettre à jour la configuration horaire", response_model=ConfigurationHoraireResponse)
async def update_configuration_horaire(
    groupe_id: UUID,
    config_data: ConfigurationHoraireUpdate,
    groupe_service: GroupeService = Depends(get_groupe_service),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    try:
        config = groupe_service.update_configuration_horaire(groupe_id, config_data, current_user)
        return config
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/configuration-horaire/{config_id}", summary="Supprimer une configuration horaire")
async def delete_configuration_horaire(
    config_id: UUID,
    groupe_service: GroupeService = Depends(get_groupe_service),
    current_user: EmployeDB = Depends(get_current_active_admin)
):
    try:
        groupe_service.delete_configuration_horaire(config_id, current_user)
        return {"message": "Configuration horaire supprimée avec succès."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
