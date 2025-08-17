from uuid import UUID
from fastapi import HTTPException, status
from typing import List
from app.repositories.poste_repository import PosteRepository
from sqlalchemy.orm import Session
from app.schemas.schemas import PosteCreate, PosteUpdate, PosteResponse
from app.models import EmployeDB

class PosteService:
    def __init__(self, db: Session):
        self.db = db
        self.poste_repo = PosteRepository(db)

    def create_poste(self, poste_data: PosteCreate, current_user: EmployeDB) -> PosteResponse:
        if current_user.role not in ("admin", "super-admin"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Non autorisé à créer un poste.")

        existing = self.poste_repo.get_poste_by_name_and_company(poste_data.nom, poste_data.idEntreprise)
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Un poste avec ce nom existe déjà dans l'entreprise.")

        db_poste = self.poste_repo.create_poste(poste_data.model_dump())
        return PosteResponse.model_validate(db_poste)

    def get_poste(self, poste_id: UUID, current_user: EmployeDB) -> PosteResponse:
        poste = self.poste_repo.get_poste_by_id(poste_id)
        if not poste:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Poste non trouvé.")
        # Contrôle d'accès : vérifier que le poste appartient à l'entreprise de l'utilisateur
        if current_user.idEntreprise != poste.idEntreprise:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Accès refusé au poste.")
        return PosteResponse.model_validate(poste)

    def list_postes(self, idEntreprise: UUID, current_user: EmployeDB, skip=0, limit=100) -> List[PosteResponse]:
        if current_user.role not in ("admin", "super-admin"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Non autorisé à lister les postes.")
        postes = self.poste_repo.list_postes(idEntreprise, skip, limit)
        return [PosteResponse.model_validate(p) for p in postes]

    def update_poste(self, poste_id: UUID, update_data: PosteUpdate, current_user: EmployeDB) -> PosteResponse:
        poste = self.poste_repo.get_poste_by_id(poste_id)
        if not poste:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Poste non trouvé.")
        if current_user.idEntreprise != poste.idEntreprise:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Non autorisé à modifier ce poste.")

        if update_data.nom and update_data.nom != poste.nom:
            existing = self.poste_repo.get_poste_by_name_and_company(update_data.nom, poste.idEntreprise)
            if existing:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="Nom de poste déjà utilisé dans l’entreprise.")

        update_dict = update_data.model_dump(exclude_unset=True)
        updated = self.poste_repo.update_poste(poste, update_dict)
        return PosteResponse.model_validate(updated)

    def delete_poste(self, poste_id: UUID, current_user: EmployeDB):
        poste = self.poste_repo.get_poste_by_id(poste_id)
        if not poste:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Poste non trouvé.")
        if current_user.idEntreprise != poste.idEntreprise:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Non autorisé à supprimer ce poste.")
        # Optionnel : vérifier employés liés au poste avant suppression
        self.poste_repo.delete_poste(poste)
