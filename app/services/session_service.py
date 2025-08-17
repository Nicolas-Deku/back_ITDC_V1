from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from app.models import SessionDB, EmployeDB
from app.repositories.session_repository import SessionRepository
from app.schemas.schemas import SessionResponse
from app.core.security import create_access_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self, db: Session):
        self.repository = SessionRepository(db)

    def create_session(self, employe: EmployeDB, expires_in_minutes: int = 60) -> SessionResponse:
        """
        Crée une nouvelle session pour un employé.

        Args:
            employe: Employé authentifié.
            expires_in_minutes: Durée d'expiration de la session en minutes.

        Returns:
            SessionResponse: Détails de la session créée.
        """
        access_token = create_access_token(
            data={
                "sub": str(employe.idEmploye),
                "email": employe.email,
                "idEmploye": str(employe.idEmploye),
                "employee_id": employe.employeeId,
                "company_id": str(employe.idEntreprise) if employe.idEntreprise else None,
                "company": employe.entreprise.nom if employe.entreprise else None,
                "role": employe.role,
                "idGroupe": str(employe.idGroupe) if employe.idGroupe else None
            },
            expires_delta=timedelta(minutes=expires_in_minutes)
        )
        session = self.repository.create_session(employe, access_token, expires_in_minutes)
        logger.info(f"Session créée pour employé {employe.email}")
        return self._map_session_to_response(session)

    def get_session_by_id(self, session_id: UUID, current_user: EmployeDB) -> SessionResponse:
        """
        Récupère une session par son ID.

        Args:
            session_id: ID de la session.
            current_user: Utilisateur authentifié.

        Returns:
            SessionResponse: Détails de la session.

        Raises:
            HTTPException: Si la session n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        session = self.repository.get_session_by_id(session_id)
        if not session:
            logger.error(f"Session avec ID {session_id} non trouvée.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session non trouvée.")
        if current_user.idEmploye != session.idEmploye and current_user.role not in ["admin", "manager"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à accéder à la session {session_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à accéder à cette session."
            )
        return self._map_session_to_response(session)

    def get_sessions_by_employe_id(self, employe_id: UUID, current_user: EmployeDB) -> List[SessionResponse]:
        """
        Récupère toutes les sessions actives d'un employé.

        Args:
            employe_id: ID de l'employé.
            current_user: Utilisateur authentifié.

        Returns:
            List[SessionResponse]: Liste des sessions actives.

        Raises:
            HTTPException: Si l'employé n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        employe = self.repository.db.query(EmployeDB).filter(EmployeDB.idEmploye == employe_id).first()
        if not employe:
            logger.error(f"Employé avec ID {employe_id} non trouvé.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé.")
        if current_user.idEmploye != employe_id and current_user.role not in ["admin", "manager"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à accéder aux sessions de l'employé {employe_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à accéder aux sessions de cet employé."
            )
        sessions = self.repository.get_sessions_by_employe_id(employe_id)
        return [self._map_session_to_response(s) for s in sessions]

    def revoke_session(self, session_id: UUID, current_user: EmployeDB) -> dict:
        """
        Révoque une session.

        Args:
            session_id: ID de la session.
            current_user: Utilisateur authentifié.

        Returns:
            dict: Message de confirmation.

        Raises:
            HTTPException: Si la session n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        session = self.repository.get_session_by_id(session_id)
        if not session:
            logger.error(f"Session avec ID {session_id} non trouvée.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session non trouvée.")
        if current_user.idEmploye != session.idEmploye and current_user.role not in ["admin", "manager"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à révoquer la session {session_id}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à révoquer cette session."
            )
        self.repository.revoke_session(session)
        logger.info(f"Session révoquée : {session_id} par {current_user.email}")
        return {"message": "Session révoquée avec succès."}

    def cleanup_expired_sessions(self) -> dict:
        """
        Supprime les sessions expirées.

        Returns:
            dict: Message de confirmation.
        """
        self.repository.cleanup_expired_sessions()
        return {"message": "Sessions expirées nettoyées avec succès."}

    def _map_session_to_response(self, session: SessionDB) -> SessionResponse:
        """
        Mappe un objet SessionDB à un modèle Pydantic SessionResponse.
        """
        return SessionResponse(
            idSession=session.idSession,
            idEmploye=session.idEmploye,
            access_token=session.access_token,
            token_type=session.token_type,
            date_creation=session.date_creation,
            date_expiration=session.date_expiration,
            is_active=session.is_active
        )