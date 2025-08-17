import asyncio
import random
from typing import Dict
from pydantic import EmailStr
from datetime import timedelta
from fastapi import HTTPException, status
import logging

from app.repositories.employe_repository import EmployeRepository
from app.core.security import create_access_token, verify_password
from app.schemas.schemas import LoginCredentials, SendCodeRequest, VerifyCodeRequest

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, user_repo: EmployeRepository):
        self.user_repo = user_repo

    def _normalize_identifier(self, identifier: str, id_type: str) -> str:
        """Normalise l'identifiant selon son type (email en minuscules, sms nettoyé)."""
        if id_type == "email":
            return identifier.strip().lower()
        elif id_type == "sms":
            return identifier.strip()
        return identifier.strip()

    async def authenticate_user(self, credentials: LoginCredentials) -> Dict:
        email_received = credentials.email.strip().lower()
        password_received = credentials.password.strip()

        user = self.user_repo.get_employe_by_email(email_received)
        if not user:
            logger.warning(f"Tentative d'authentification échouée : email {email_received} non trouvé")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Email incorrect ou utilisateur non trouvé.")

        try:
            if not verify_password(password_received, user.motDePasse):
                logger.warning(f"Tentative d'authentification échouée : mot de passe incorrect pour {email_received}")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Mot de passe incorrect.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la vérification du mot de passe: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Erreur lors de la vérification du mot de passe.")

        token_data = {
            "sub": str(user.idEmploye),
            "email": email_received,
            "idEmploye": str(user.idEmploye),
            "employee_id": user.employeeId,
            "company_id": str(user.idEntreprise) if user.idEntreprise else None,
            "company": user.entreprise.nom if user.entreprise else None,
            "role": user.role
        }

        access_token = create_access_token(data=token_data, expires_delta=timedelta(minutes=60))

        logger.info(f"Utilisateur {email_received} authentifié avec succès")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            **token_data
        }

    async def send_login_code(self, request: SendCodeRequest) -> Dict:
        normalized_id = self._normalize_identifier(request.identifier, request.type)

        if request.type == "email":
            user = self.user_repo.get_employe_by_email(normalized_id)
        elif request.type == "sms":
            user = self.user_repo.get_employe_by_phone(normalized_id)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type invalide")

        if not user:
            logger.warning(f"Identifiant {normalized_id} ({request.type}) non enregistré")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Identifiant non enregistré")

        code = str(random.randint(100000, 999999))

        # Stockage persistant en base avec expiration 4 minutes
        self.user_repo.set_verification_code(normalized_id, code, expires_in_minutes=4)

        message = (
            f"Un code a été envoyé à votre e-mail : {normalized_id}."
            if request.type == "email"
            else f"Un code a été envoyé par SMS au : {normalized_id}."
        )

        logger.info(f"Code de vérification envoyé à {normalized_id} ({request.type}) : {code}")
        await asyncio.sleep(1)  # simulation délai

        return {"message": message}

    async def verify_login_code(self, request: VerifyCodeRequest) -> Dict:
        normalized_id = self._normalize_identifier(request.identifier, request.type)
        stored_code = self.user_repo.get_verification_code(normalized_id)

        if not stored_code:
            logger.warning(f"Aucun code trouvé ou expiré pour {normalized_id} ({request.type})")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aucun code envoyé ou expiré")

        if stored_code != request.code:
            logger.warning(f"Code incorrect pour {normalized_id} ({request.type})")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Code incorrect")

        self.user_repo.delete_verification_code(normalized_id)

        if request.type == "email":
            user_email = EmailStr(normalized_id)
        else:
            user = self.user_repo.get_employe_by_phone(normalized_id)
            if not user:
                logger.warning(f"Numéro {normalized_id} non reconnu après vérification")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Numéro non reconnu")
            user_email = EmailStr(user.email)

        user = self.user_repo.get_employe_by_email(user_email)
        if not user:
            logger.warning(f"Utilisateur introuvable pour {user_email} après vérification")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

        token_data = {
            "sub": str(user.idEmploye),
            "email": str(user_email),
            "idEmploye": str(user.idEmploye),
            "employee_id": user.employeeId,
            "company_id": str(user.idEntreprise) if user.idEntreprise else None,
            "company": user.entreprise.nom if user.entreprise else None,
            "role": user.role
        }

        access_token = create_access_token(data=token_data, expires_delta=timedelta(minutes=30))

        logger.info(f"Code vérifié avec succès pour {user_email}, JWT généré")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            **token_data
        }
