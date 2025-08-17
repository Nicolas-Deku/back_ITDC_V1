from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.models import SessionDB, EmployeDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionRepository:
    """
    Gère les opérations de persistance des données pour les sessions d'authentification.
    """
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, employe: EmployeDB, access_token: str, expires_in_minutes: int) -> SessionDB:
        """
        Crée une nouvelle session pour un employé.

        Args:
            employe: Employé associé à la session.
            access_token: Token JWT de la session.
            expires_in_minutes: Durée d'expiration de la session en minutes.

        Returns:
            SessionDB: Session créée.
        """
        expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
        db_session = SessionDB(
            idEmploye=employe.idEmploye,
            access_token=access_token,
            token_type="bearer",
            date_expiration=expires_at,
            is_active=True
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        logger.info(f"Session créée pour employé {employe.email} avec ID {db_session.idSession}")
        return db_session

    def get_session_by_id(self, session_id: UUID) -> Optional[SessionDB]:
        """
        Récupère une session par son ID.

        Args:
            session_id: ID de la session.

        Returns:
            SessionDB: Session trouvée ou None si non trouvée.
        """
        session = self.db.query(SessionDB).filter(SessionDB.idSession == session_id).first()
        if session:
            logger.info(f"Session récupérée : {session_id}")
        return session

    def get_sessions_by_employe_id(self, employe_id: UUID) -> List[SessionDB]:
        """
        Récupère toutes les sessions actives d'un employé.

        Args:
            employe_id: ID de l'employé.

        Returns:
            List[SessionDB]: Liste des sessions actives.
        """
        sessions = self.db.query(SessionDB).filter(
            SessionDB.idEmploye == employe_id,
            SessionDB.is_active == True,
            SessionDB.date_expiration > datetime.now()
        ).all()
        logger.info(f"{len(sessions)} sessions actives récupérées pour employé {employe_id}")
        return sessions

    def revoke_session(self, session: SessionDB):
        """
        Révoque une session (marque comme inactive).

        Args:
            session: Session à révoquer.
        """
        session.is_active = False
        self.db.commit()
        self.db.refresh(session)
        logger.info(f"Session révoquée : {session.idSession}")

    def cleanup_expired_sessions(self):
        """
        Supprime les sessions expirées ou inactives.
        """
        expired_count = self.db.query(SessionDB).filter(
            SessionDB.date_expiration <= datetime.now()
        ).delete()
        self.db.commit()
        logger.info(f"{expired_count} sessions expirées supprimées")