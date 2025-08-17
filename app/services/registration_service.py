from typing import Dict, Optional
from pydantic import EmailStr
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import secrets
import json
from datetime import datetime, timedelta, timezone
import logging
import uuid
from app.models import EmployeDB
from app.repositories.employe_repository import EmployeRepository
from app.services.entreprise_service import EntrepriseService
from app.services.employe_service import EmployeService
from app.services.poste_service import PosteService  # service pour poste

from app.schemas.schemas import (
    PersonalInfo,
    CompanyInfo,
    UserVerification,
    CompanyVerification,
    FinalRegistrationData,
    EmployeResponse,
    MessageResponse,
    EntrepriseCreate,
    EmployeCreate,
    PosteCreate,
)
from app.utils.email_sender import send_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RegistrationService:
    def __init__(self, db: Session):
        self.db = db
        self.employe_repo = EmployeRepository(db)
        self.entreprise_service = EntrepriseService(db)
        self.employe_service = EmployeService(db)
        self.poste_service = PosteService(db)  # instanciation du service poste

    # 1) Enregistrement infos personnelles + position dans pending
    async def process_personal_info(self, personal_info: PersonalInfo) -> MessageResponse:
        try:
            if self.employe_repo.get_employe_by_email(personal_info.userEmail):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "L'email est déjà enregistré")
            if self.employe_repo.get_employe_by_employee_id(personal_info.employeeId):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "L'ID d'employé est déjà enregistré")
            existing_code = self.employe_repo.get_verification_code(personal_info.userEmail)
            if existing_code:
                raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Un code a déjà été envoyé, veuillez patienter")
            verification_code = secrets.token_hex(3)
            expires_at = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(minutes=4)
            self.employe_repo.set_verification_code(personal_info.userEmail, verification_code, 4)

            # Sauvegarde complète y compris 'position' (nom du poste)
            self.employe_repo.add_pending_registration(
                personal_info.userEmail, personal_info.model_dump(), expires_at
            )
            subject = "Code de vérification BioTrack"
            body = f"Votre code de vérification est : {verification_code}\nValidité : 4 minutes."
            await send_email(personal_info.userEmail, subject, body)
            return MessageResponse(
                message=f"Code envoyé à {personal_info.userEmail}",
                expires_at=expires_at.isoformat(),
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur lors de process_personal_info: {e}")
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erreur serveur : {e}")

    # 2) Vérification code email perso
    async def verify_user_email(self, verification_data: UserVerification) -> MessageResponse:
        stored_code = self.employe_repo.get_verification_code(verification_data.email)
        if not stored_code:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code introuvable ou expiré")
        if stored_code != verification_data.code:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code incorrect")
        pending = self.employe_repo.get_pending_registration(verification_data.email)
        if not pending:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Inscription introuvable")
        self.employe_repo.delete_verification_code(verification_data.email)
        current_info = {}
        personal_info_raw = pending.get("personal_info_json")
        if personal_info_raw:
            if isinstance(personal_info_raw, str):
                current_info = json.loads(personal_info_raw)
            elif isinstance(personal_info_raw, dict):
                current_info = personal_info_raw
        current_info["status"] = "email_verified"
        self.employe_repo.update_pending_registration(verification_data.email, "personal_info", current_info)
        return MessageResponse(
            message="Email vérifié, veuillez fournir les informations de l'entreprise.",
            expires_at=pending.get("expires_at").isoformat() if pending.get("expires_at") else None,
        )

    # 3) Traitement infos entreprise : enregistrement pending + envoi code
    async def process_company_info(self, company_info: CompanyInfo, user_email: EmailStr) -> MessageResponse:
        pending = self.employe_repo.get_pending_registration(user_email)
        if not pending:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Inscription introuvable")
        personal_info = pending.get("personal_info_json")
        if not personal_info or personal_info.get("status") != "email_verified":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email non vérifié")
        existing_code = self.employe_repo.get_verification_code(company_info.companyContactEmail)
        if existing_code:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Un code pour l'entreprise a déjà été envoyé, veuillez patienter")
        self.employe_repo.update_pending_registration(user_email, "company_info", company_info.model_dump())
        verification_code = secrets.token_hex(2)
        expires_at = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(minutes=4)
        self.employe_repo.set_verification_code(company_info.companyContactEmail, verification_code, 4)
        try:
            subject = "Code de vérification BioTrack"
            body = f"Votre code de vérification pour l'entreprise est : {verification_code}\nValidité : 4 minutes."
            await send_email(company_info.companyContactEmail, subject, body)
            return MessageResponse(
                message=f"Code envoyé à {company_info.companyContactEmail}",
                expires_at=expires_at.isoformat(),
            )
        except Exception as e:
            logger.error(f"Erreur envoi mail company info: {e}")
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erreur envoi mail: {e}")

    # 4) Vérification code email entreprise + update rôle
    async def verify_company_email(self, verification_data: CompanyVerification) -> MessageResponse:
        pending = self.employe_repo.get_pending_registration(verification_data.userEmail)
        if not pending or "company_info_json" not in pending:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Infos entreprise manquantes")
        company_email = None
        company_info_raw = pending.get("company_info_json")
        if company_info_raw and isinstance(company_info_raw, dict):
            company_email = company_info_raw.get("companyContactEmail")
        stored_code = self.employe_repo.get_verification_code(company_email)
        if not stored_code:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code introuvable ou expiré")
        if stored_code != verification_data.companyCode:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code incorrect")
        self.employe_repo.delete_verification_code(company_email)
        self.employe_repo.update_pending_registration(verification_data.userEmail, "role_assigned", "admin")

        # Ici on ne crée pas le poste car entreprise peut ne pas être encore générée, poste créé dans complete_registration

        return MessageResponse(
            message="Entreprise vérifiée, veuillez finaliser inscription.",
            expires_at=pending.get("expires_at").isoformat() if pending.get("expires_at") else None,
        )

    # 5) Finalisation inscription : création entreprise, poste, employé
    async def complete_registration(self, registration_data: FinalRegistrationData) -> EmployeResponse:
        pending = self.employe_repo.get_pending_registration(registration_data.userEmail)
        if not pending:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Inscription expirée ou introuvable")
        personal_info = pending.get("personal_info_json")
        if not personal_info or personal_info.get("status") != "email_verified":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email non vérifié")

        poste_id: Optional[uuid.UUID] = None

        if registration_data.position:
            idEntreprise_for_poste = None

            if pending.get("role_assigned") == "admin":
                # Si admin -> entreprise sera créée, pas encore disponible ici pour poste
                # Option : créer poste après création entreprise (juste après create_entreprise)
                pass
            else:
                # Utilisateur non admin : on récupère idEntreprise via idGroupe
                if registration_data.idGroupe:
                    groupe = self.employe_repo.get_groupe_by_id(registration_data.idGroupe)
                    if not groupe:
                        raise HTTPException(status.HTTP_404_NOT_FOUND, "Groupe introuvable")
                    idEntreprise_for_poste = groupe.idEntreprise
                else:
                    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Groupe requis pour récupérer entreprise")

            # Si entreprise disponible, recherche ou création poste
            if idEntreprise_for_poste:
                poste_obj = self.poste_service.get_poste_by_name_and_company(registration_data.position, idEntreprise_for_poste)
                if not poste_obj:
                    poste_create = PosteCreate(
                        nom=registration_data.position,
                        description=None,
                        idEntreprise=idEntreprise_for_poste
                    )
                    # Création poste avec role d'utilisateur courant à défaut "employee"
                    temp_user = EmployeDB(email=registration_data.userEmail, role=pending.get("role_assigned", "employee"))
                    poste_obj = self.poste_service.create_poste(poste_create, current_user=temp_user)
                poste_id = poste_obj.idPoste

        employe_dict = {
            "nom": registration_data.lastName,
            "prenom": registration_data.firstName,
            "employeeId": registration_data.employeeId,
            "email": registration_data.userEmail,
            "idPoste": poste_id,
            "phone_number": registration_data.phoneNumber,
            "motDePasse": registration_data.password if registration_data.password else None,
            "role": pending.get("role_assigned", "employee"),
        }

        if pending.get("role_assigned") == "admin":
            if not registration_data.companyName or not registration_data.companyContactEmail:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Infos entreprise requises pour admin")
            entreprise_data = EntrepriseCreate(
                nom=registration_data.companyName,
                contact_email=registration_data.companyContactEmail.lower(),
                adresse=registration_data.adresse,
            )
            temp_user = EmployeDB(email=registration_data.userEmail, role="admin")
            entreprise = self.entreprise_service.create_entreprise(entreprise_data, temp_user)
            employe_dict["idEntreprise"] = entreprise.idEntreprise
            employe_dict["idGroupe"] = None

            # **CREATION DU POSTE POUR ADMIN APRES ENTREPRISE CREEE**
            # Si poste non créé précédemment et qu'on a le nom
            if registration_data.position and poste_id is None:
                poste_create = PosteCreate(
                    nom=registration_data.position,
                    description=None,
                    idEntreprise=entreprise.idEntreprise
                )
                poste_obj = self.poste_service.create_poste(poste_create, current_user=temp_user)
                employe_dict["idPoste"] = poste_obj.idPoste

        else:
            if not registration_data.idGroupe:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Groupe requis pour employés non admin")
            groupe = self.employe_repo.get_groupe_by_id(registration_data.idGroupe)
            if not groupe:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Groupe introuvable")
            employe_dict["idEntreprise"] = groupe.idEntreprise
            employe_dict["idGroupe"] = groupe.idGroupe

        employe_create_obj = EmployeCreate(**employe_dict)
        current_user = EmployeDB(email=registration_data.userEmail, role=employe_dict.get("role"))

        employe = self.employe_service.create_employe(employe_create_obj, current_user)

        self.employe_repo.delete_pending_registration(registration_data.userEmail)
        self.employe_repo.add_pending_registration(
            registration_data.userEmail,
            {"status": "pending_fingerprint_validation"},
            datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(days=1),
        )
        response = EmployeResponse.model_validate(employe)
        response.message = "Inscription terminée, veuillez enregistrer votre empreinte digitale."
        response.expires_at = (
            pending.get("expires_at").isoformat() if pending.get("expires_at") else None
        )
        return response

    async def complete_fingerprint_validation(self, user_email: EmailStr) -> None:
        pending = self.employe_repo.get_pending_registration(user_email)
        if not pending:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Inscription introuvable")
        if pending.get("personal_info_json", {}).get("status") != "pending_fingerprint_validation":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Validation empreinte en attente absente")
        self.employe_repo.delete_pending_registration(user_email)

    async def get_pending_state(self, user_email: EmailStr) -> Dict:
        pending = self.employe_repo.get_pending_registration(user_email)
        if not pending:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Aucune inscription en cours")
        step = "personal_info"
        if pending.get("personal_info_json") and pending["personal_info_json"].get("status") == "email_verified":
            step = "company_info"
        if pending.get("company_info_json"):
            step = "verify_company"
        if pending.get("role_assigned") == "admin":
            step = "final"
        if pending.get("personal_info_json", {}).get("status") == "pending_fingerprint_validation":
            step = "fingerprint_validation"
        return {
            "step": step,
            "user_email": user_email,
            "personal_info": pending.get("personal_info_json"),
            "company_info": pending.get("company_info_json"),
            "role": pending.get("role_assigned"),
            "expires_at": pending.get("expires_at").isoformat() if pending.get("expires_at") else None,
        }
