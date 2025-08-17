from typing import Optional, Dict
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from app.models import EntrepriseDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntrepriseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_entreprise_by_id(self, entreprise_id: UUID) -> Optional[EntrepriseDB]:
        entreprise = self.db.query(EntrepriseDB).filter(EntrepriseDB.idEntreprise == entreprise_id).first()
        if entreprise:
            logger.info(f"Entreprise récupérée par ID : {entreprise_id}")
        return entreprise

    def get_entreprise_by_name(self, name: str) -> Optional[EntrepriseDB]:
        entreprise = self.db.query(EntrepriseDB).filter(EntrepriseDB.nom == name).first()
        if entreprise:
            logger.info(f"Entreprise récupérée par nom : {name}")
        return entreprise

    def create_entreprise(self, entreprise_data: Dict) -> EntrepriseDB:
        db_entreprise = EntrepriseDB(
            nom=entreprise_data["nom"],
            adresse=entreprise_data.get("adresse"),
            contact_email=entreprise_data.get("contact_email").lower() if entreprise_data.get("contact_email") else None
        )
        self.db.add(db_entreprise)
        self.db.commit()
        self.db.refresh(db_entreprise)
        logger.info(f"Entreprise créée : {db_entreprise.nom}")
        return db_entreprise

    def update_entreprise(self, entreprise: EntrepriseDB, update_data: Dict) -> EntrepriseDB:
        for field, value in update_data.items():
            if hasattr(entreprise, field):
                if field == "contact_email" and isinstance(value, str):
                    value = value.lower()
                setattr(entreprise, field, value)
        self.db.commit()
        self.db.refresh(entreprise)
        logger.info(f"Entreprise mise à jour : {entreprise.nom}")
        return entreprise

    def delete_entreprise(self, entreprise: EntrepriseDB):
        self.db.delete(entreprise)
        self.db.commit()
        logger.info(f"Entreprise supprimée : {entreprise.nom}")