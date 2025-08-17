from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from app.repositories.entreprise_repository import EntrepriseRepository
from app.schemas.schemas import EntrepriseCreate, EntrepriseUpdate, EntrepriseResponse
from app.models import EmployeDB, EntrepriseDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntrepriseService:
    def __init__(self, db: Session):
        self.db = db
        self.entreprise_repo = EntrepriseRepository(db)

    def create_entreprise(self, entreprise_data: EntrepriseCreate, current_user: EmployeDB) -> EntrepriseResponse:
        if current_user.role != "admin":
            logger.error(f"Utilisateur {current_user.email} non autorisé à créer une entreprise.")
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Seul un admin peut créer une entreprise.")

        existing_entreprise = self.entreprise_repo.get_entreprise_by_name(entreprise_data.nom)
        if existing_entreprise:
            msg = f"Entreprise avec le nom « {entreprise_data.nom} » existe déjà."
            logger.warning(msg)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=msg
            )
        db_entreprise = self.entreprise_repo.create_entreprise(entreprise_data.model_dump())
        logger.info(f"Entreprise créée : {db_entreprise.nom} par {current_user.email}")
        return EntrepriseResponse.model_validate(db_entreprise)


    def get_entreprise(self, entreprise_id: UUID, current_user: EmployeDB) -> EntrepriseResponse:
        entreprise = self.entreprise_repo.get_entreprise_by_id(entreprise_id)
        if not entreprise:
            logger.error(f"Entreprise avec ID {entreprise_id} non trouvée.")
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Entreprise non trouvée")
        if current_user.idEntreprise and current_user.idEntreprise != entreprise_id:
            logger.error(f"Utilisateur {current_user.email} non autorisé à accéder à l'entreprise {entreprise_id}.")
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Vous n'êtes pas autorisé à accéder à cette entreprise.")
        return EntrepriseResponse.model_validate(entreprise)

    def list_entreprises(self, current_user: EmployeDB, skip: int = 0, limit: int = 100) -> List[EntrepriseResponse]:
        if current_user.role != "admin":
            logger.error(f"Utilisateur {current_user.email} non autorisé à lister les entreprises.")
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Seul un admin peut lister les entreprises.")
        entreprises = self.db.query(EntrepriseDB).offset(skip).limit(limit).all()
        return [EntrepriseResponse.model_validate(e) for e in entreprises]

    def update_entreprise(self, entreprise_id: UUID, update_data: EntrepriseUpdate, current_user: EmployeDB) -> EntrepriseResponse:
        entreprise = self.entreprise_repo.get_entreprise_by_id(entreprise_id)
        if not entreprise:
            logger.error(f"Entreprise ID {entreprise_id} non trouvée.")
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Entreprise non trouvée")
        if current_user.idEntreprise and current_user.idEntreprise != entreprise_id:
            logger.error(f"Utilisateur {current_user.email} non autorisé à modifier l'entreprise {entreprise_id}.")
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Vous n'êtes pas autorisé à modifier cette entreprise.")
        if update_data.nom and update_data.nom != entreprise.nom:
            existing = self.entreprise_repo.get_entreprise_by_name(update_data.nom)
            if existing:
                logger.error(f"Entreprise avec le nom {update_data.nom} existe déjà.")
                raise HTTPException(status.HTTP_409_CONFLICT, "Une entreprise avec ce nom existe déjà.")
        update_dict = update_data.model_dump(exclude_unset=True)
        updated = self.entreprise_repo.update_entreprise(entreprise, update_dict)
        logger.info(f"Entreprise mise à jour : {updated.nom} par {current_user.email}")
        return EntrepriseResponse.model_validate(updated)

    def delete_entreprise(self, entreprise_id: UUID, current_user: EmployeDB):
        entreprise = self.entreprise_repo.get_entreprise_by_id(entreprise_id)
        if not entreprise:
            logger.error(f"Entreprise ID {entreprise_id} non trouvée.")
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Entreprise non trouvée")
        if current_user.idEntreprise and current_user.idEntreprise != entreprise_id:
            logger.error(f"Utilisateur {current_user.email} non autorisé à supprimer l'entreprise {entreprise_id}.")
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Vous n'êtes pas autorisé à supprimer cette entreprise.")
        employees_count = self.db.query(EmployeDB).filter(EmployeDB.idEntreprise == entreprise_id).count()
        if employees_count > 0:
            logger.error(f"Impossible de supprimer entreprise {entreprise_id} : {employees_count} employés associés.")
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Impossible de supprimer une entreprise avec des employés associés.")
        self.entreprise_repo.delete_entreprise(entreprise)
        logger.info(f"Entreprise supprimée : {entreprise.nom} par {current_user.email}")
