from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from app.models import EmpreinteDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmpreinteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_empreinte(self, id_employe: UUID, biometric_data: bytes) -> EmpreinteDB:
        db_empreinte = EmpreinteDB(
            idEmploye=id_employe,
            donneesBiometriques=biometric_data
        )
        self.db.add(db_empreinte)
        self.db.commit()
        self.db.refresh(db_empreinte)
        logger.info(f"Empreinte créée pour employé {id_employe}")
        return db_empreinte

    def get_empreintes_by_employe_id(self, id_employe: UUID) -> List[EmpreinteDB]:
        empreintes = self.db.query(EmpreinteDB).filter(EmpreinteDB.idEmploye == id_employe).all()
        logger.info(f"{len(empreintes)} empreintes récupérées pour employé {id_employe}")
        return empreintes

    def get_empreinte_by_id(self, id_empreinte: UUID) -> Optional[EmpreinteDB]:
        empreinte = self.db.query(EmpreinteDB).filter(EmpreinteDB.idEmpreinte == id_empreinte).first()
        if empreinte:
            logger.info(f"Empreinte {id_empreinte} récupérée")
        return empreinte

    def delete_empreinte(self, id_empreinte: UUID):
        empreinte = self.get_empreinte_by_id(id_empreinte)
        if not empreinte:
            logger.warning(f"Tentative de suppression d'une empreinte inexistante : {id_empreinte}")
            return
        self.db.delete(empreinte)
        self.db.commit()
        logger.info(f"Empreinte {id_empreinte} supprimée")