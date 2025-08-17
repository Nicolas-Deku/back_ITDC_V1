from sqlalchemy.orm import Session
from uuid import UUID
from app.models import PosteDB
from app.schemas.schemas import PosteCreate, PosteUpdate

class PosteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_poste_by_id(self, poste_id: UUID) -> PosteDB | None:
        return self.db.query(PosteDB).filter(PosteDB.idPoste == poste_id).first()

    def get_poste_by_name_and_company(self, nom: str, idEntreprise: UUID) -> PosteDB | None:
        return (
            self.db.query(PosteDB)
            .filter(PosteDB.nom == nom, PosteDB.idEntreprise == idEntreprise)
            .first()
        )

    def list_postes(self, idEntreprise: UUID, skip: int = 0, limit: int = 100) -> list[PosteDB]:
        return (
            self.db.query(PosteDB)
            .filter(PosteDB.idEntreprise == idEntreprise)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_poste(self, data: dict) -> PosteDB:
        poste = PosteDB(**data)
        self.db.add(poste)
        self.db.commit()
        self.db.refresh(poste)
        return poste

    def update_poste(self, poste: PosteDB, data: dict) -> PosteDB:
        for key, value in data.items():
            setattr(poste, key, value)
        self.db.commit()
        self.db.refresh(poste)
        return poste

    def delete_poste(self, poste: PosteDB):
        self.db.delete(poste)
        self.db.commit()
