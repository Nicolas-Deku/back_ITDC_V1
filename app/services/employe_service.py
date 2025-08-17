from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
import secrets
from uuid import UUID, uuid4  # ✅ Ajout uuid4
import logging

from app.repositories.employe_repository import EmployeRepository
from app.services.entreprise_service import EntrepriseService
from app.services.empreinte_service import EmpreinteService
from app.services.groupe_service import GroupeService
from app.services.poste_service import PosteService
from app.schemas.schemas import (
    EmployeCreate, EmployeUpdate, EmployeResponse,
    PresenceResponse, EntrepriseCreate, MessageResponse,
    FingerprintScanRequest, Notification
)
from app.models import EmployeDB
from app.core.security import get_password_hash
from app.websocket.websocket import web_notification_manager, desktop_notification_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmployeService:
    def __init__(self, db: Session):
        self.db = db
        self.employe_repo = EmployeRepository(db)
        self.entreprise_service = EntrepriseService(db)
        self.empreinte_service = EmpreinteService(db)
        self.groupe_service = GroupeService(db)
        self.poste_service = PosteService(db)

    async def create_employe(self, employe_data: EmployeCreate, current_user: EmployeDB) -> EmployeResponse:
        email_lower = employe_data.email.lower()
        logger.info(f"Donnée reçue pour création employé : {employe_data}")

        # 🔹 Vérif droits
        if employe_data.motDePasse and current_user.role not in ["admin", "manager"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Seuls les admins ou managers peuvent définir un mot de passe.")

        # 🔹 Vérif unicité email / employeeId / téléphone
        if self.employe_repo.get_employe_by_email(email_lower):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="L'email est déjà enregistré")
        if self.employe_repo.get_employe_by_employee_id(employe_data.employeeId):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="L'ID d'employé est déjà enregistré")
        if employe_data.phone_number and self.employe_repo.get_employe_by_phone_number(employe_data.phone_number):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le numéro de téléphone est déjà enregistré")

        # 🔹 Vérif entreprise fournie ou création nouvelle
        if not employe_data.idEntreprise and not employe_data.companyName:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="idEntreprise ou companyName doit être fourni.")

        if employe_data.companyName and not employe_data.companyContactEmail:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="companyContactEmail doit être fourni si companyName est spécifié.")

        if employe_data.idEntreprise:
            entreprise = self.entreprise_service.get_entreprise(employe_data.idEntreprise, current_user)
            if not entreprise:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entreprise non trouvée avec l'ID fourni.")
            if current_user.idEntreprise and current_user.idEntreprise != employe_data.idEntreprise:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Vous ne pouvez pas créer un employé pour une autre entreprise.")
        else:
            entreprise_data = EntrepriseCreate(
                nom=employe_data.companyName,
                contact_email=employe_data.companyContactEmail.lower()
            )
            entreprise = self.entreprise_service.create_entreprise(entreprise_data, current_user)

        # 🔹 Vérif groupe et poste
        groupe = None
        if employe_data.idGroupe:
            groupe = self.employe_repo.get_groupe_by_id(employe_data.idGroupe)
            if not groupe or groupe.idEntreprise != entreprise.idEntreprise:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Groupe invalide ou non associé à l’entreprise.")

        poste = None
        if employe_data.idPoste:
            poste = self.employe_repo.get_poste_by_id(employe_data.idPoste)
            if not poste or poste.idEntreprise != entreprise.idEntreprise:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Poste invalide ou non associé à l’entreprise.")

        # 🔹 Préparation des données EmployeDB
        employe_dict = employe_data.model_dump(exclude={"motDePasse", "companyName", "companyContactEmail", "idEntreprise"})
        employe_dict["idEntreprise"] = entreprise.idEntreprise
        employe_dict["idGroupe"] = groupe.idGroupe if groupe else None
        employe_dict["idPoste"] = poste.idPoste if poste else None

        if employe_data.motDePasse:
            employe_dict["motDePasse"] = get_password_hash(employe_data.motDePasse)
        else:
            temp_password = secrets.token_urlsafe(12)
            employe_dict["motDePasse"] = get_password_hash(temp_password)
            logger.info(f"Mot de passe temporaire généré pour {email_lower}")

        employe_dict["email"] = email_lower

        # 🔹 Création en BDD
        employe_instance = EmployeDB(**employe_dict)
        new_employe = self.employe_repo.create_employe(employe_instance)
        logger.info(f"Employé créé : {new_employe.email} par {current_user.email}")

        # 🔹 Création pending_registration
        self.employe_repo.add_pending_registration(
            user_email=new_employe.email,
            personal_info={"status": "pending_fingerprint_validation"},
            expires_at=datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(minutes=1440)
        )

        # 🔹 Préparation et envoi notification temps réel
        notification = Notification(
            id=uuid4(),  # ✅ Utilisation d'un ID unique
            idEmploye=new_employe.idEmploye,
            employeeName=f"{new_employe.prenom} {new_employe.nom}",
            department=new_employe.groupe.nom if new_employe.groupe else "Non assigné",
            message="En attente de validation d'empreinte digitale.",
            idEntreprise=new_employe.idEntreprise
        )
        await self.send_notification(notification, event_type="EMPLOYE_CREATED")  # ✅ Événement en majuscules

        # 🔹 Retour
        response = self._map_employe_to_response(new_employe)
        response.message = "Employé créé avec succès. Cliquez sur 'Valider empreinte' pour finaliser l'inscription."
        return response
    
    async def send_notification(self, notif: Notification, event_type: str = "notification"):
        """Envoie la notification via WebSocket/Web et Desktop."""
        try:
            data = notif.model_dump() if hasattr(notif, "model_dump") else notif.dict()
            logger.info(f"📤 Préparation notification WS: event={event_type}, data={data}")  # ✅ Log du payload
            company_id = str(data.get("idEntreprise") or "").lower()
            if not company_id:
                logger.warning(f"[WS] idEntreprise manquant pour {notif.employeeName}")
                return
            await web_notification_manager.send_to_company(company_id, event_type, data)
            await desktop_notification_manager.send_to_company(company_id, event_type, data)
            logger.info(f"[WS] {event_type.upper()} envoyé à {company_id} pour {notif.employeeName}")
        except Exception as e:
            logger.error(f"[WS] Erreur d'envoi notification pour {notif.employeeName} : {e}")

    def get_employe_by_id(self, idEmploye: UUID) -> EmployeResponse:
        employe = self.employe_repo.get_employe_by_id(idEmploye)
        if not employe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")
        return self._map_employe_to_response(employe)

    def list_employes(self, current_user: EmployeDB, skip: int = 0, limit: int = 100) -> List[EmployeResponse]:
        if current_user.role not in ["admin", "manager"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seuls les admins ou managers peuvent lister les employés.")
        employes = self.employe_repo.get_all_employes(skip, limit)
        return [self._map_employe_to_response(emp) for emp in employes]

    def update_employe(self, employe_id: UUID, update_data: EmployeUpdate, current_user: EmployeDB) -> EmployeResponse:
        employe = self.employe_repo.get_employe_by_id(employe_id)
        if not employe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")
        if update_data.motDePasse and current_user.role not in ["admin", "manager"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seuls les admins ou managers peuvent modifier un mot de passe.")

        update_dict = update_data.model_dump(exclude_unset=True)

        if "motDePasse" in update_dict:
            update_dict["motDePasse"] = get_password_hash(update_dict["motDePasse"])
        if "email" in update_dict:
            update_dict["email"] = update_dict["email"].lower()

        entreprise = None
        if any(k in update_dict for k in ["idEntreprise", "companyName", "companyContactEmail"]):
            if "idEntreprise" in update_dict:
                entreprise = self.entreprise_service.get_entreprise(update_dict.pop("idEntreprise"), current_user)
                if not entreprise:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entreprise non trouvée avec l'ID fourni.")
            elif "companyName" in update_dict:
                if "companyContactEmail" not in update_dict:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="companyContactEmail doit être fourni si companyName est spécifié.")
                entreprise_data = EntrepriseCreate(
                    nom=update_dict.pop("companyName"),
                    contact_email=update_dict.pop("companyContactEmail").lower()
                )
                entreprise = self.entreprise_service.create_entreprise(entreprise_data, current_user)
            if entreprise:
                update_dict["idEntreprise"] = entreprise.idEntreprise

        if "idGroupe" in update_dict:
            groupe = self.employe_repo.get_groupe_by_id(update_dict["idGroupe"])
            if not groupe or (entreprise and groupe.idEntreprise != entreprise.idEntreprise):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Groupe invalide ou non associé à l’entreprise.")

        if "idPoste" in update_dict:
            poste = self.employe_repo.get_poste_by_id(update_dict["idPoste"])
            if not poste or (entreprise and poste.idEntreprise != entreprise.idEntreprise):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Poste invalide ou non associé à l’entreprise.")

        updated_employe = self.employe_repo.update_employe(employe, update_dict)
        return self._map_employe_to_response(updated_employe)

    async def delete_employe(self, employe_id: UUID, current_user: EmployeDB) -> MessageResponse:
        employe = self.employe_repo.get_employe_by_id(employe_id)
        if not employe:
            raise HTTPException(status_code=404, detail="Employé non trouvé")

        department_name = employe.groupe.nom if employe.groupe else "Non assigné"

        # On supprime en base
        self.employe_repo.delete_employe(employe)

        # 🔹 Préparation d'un message minimal pour supprimer côté front
        removal_payload = {
            "idEmploye": employe.idEmploye,     # pour l'identifier côté front
            "id": str(uuid4()),                 # id unique de l'événement
            "idEntreprise": employe.idEntreprise
        }

        # 🔹 Push WS avec event_type dédié
        await self.send_notification(
            Notification(**removal_payload),
            event_type="NOTIFICATION_REMOVED"
        )

        return MessageResponse(message="Employé supprimé avec succès")


    def scan_fingerprint(self, scan_request: FingerprintScanRequest) -> PresenceResponse:
        employe = self.employe_repo.get_employe_by_id(scan_request.idEmploye)
        if not employe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")
        registered_fingerprints = self.empreinte_service.empreinte_repo.get_empreintes_by_employe_id(employe.idEmploye)
        if not registered_fingerprints:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aucune empreinte digitale enregistrée pour cet employé.")
        if not any(fp.donneesBiometriques == scan_request.donneesBiometriques for fp in registered_fingerprints):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Empreinte digitale non reconnue.")
        new_presence = self.employe_repo.create_presence(
            id_employe=employe.idEmploye,
            presence_type="CHECK_IN",
            method="fingerprint",
            appareil_id=scan_request.appareil_id,
            id_config_horaire=scan_request.idConfigurationHoraire
        )
        return PresenceResponse.model_validate(new_presence)

    async def validate_fingerprint_manual(self, idEmploye: UUID, scan_data: FingerprintScanRequest) -> MessageResponse:
        return self.empreinte_service.validate_fingerprint(scan_data)

    def get_employe_presences(self, employe_id: UUID, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[PresenceResponse]:
        employe = self.employe_repo.get_employe_by_id(employe_id)
        if not employe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")
        presences = self.employe_repo.get_presences_by_employe_id(employe_id, start_date, end_date)
        return [PresenceResponse.model_validate(p) for p in presences]

    def list_employes_by_entreprise(
            self, idEntreprise: UUID, current_user: EmployeDB, skip: int = 0, limit: int = 100
        ) -> List[EmployeResponse]:
        if current_user.role not in ["admin", "manager"]:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Seuls les admins ou managers peuvent lister les employés par entreprise."
            )
        if current_user.idEntreprise != idEntreprise and current_user.role != "super-admin":
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Accès refusé pour lister les employés de cette entreprise."
            )
        employes = self.employe_repo.get_employes_by_entreprise(idEntreprise, skip, limit)
        return [self._map_employe_to_response(emp) for emp in employes]

    async def get_pending_fingerprint_notifications(self, current_user, entreprise_id: UUID) -> List[Notification]:
        if not entreprise_id:
            raise HTTPException(status_code=400, detail="Entreprise ID requis")
        pending_employees = self.employe_repo.get_employees_without_fingerprint(entreprise_id)
        notifications: List[Notification] = []
        for employe in pending_employees:
            department_name = employe.groupe.nom if employe.groupe else "N/A"
            notification = Notification(
                id=uuid4(),  # ✅ ID unique
                idEmploye=employe.idEmploye,
                employeeName=f"{employe.prenom} {employe.nom}",
                department=department_name,
                message="En attente de validation d'empreinte digitale.",
                idEntreprise=entreprise_id
            )
            notifications.append(notification)
        return notifications

    def _map_employe_to_response(self, employe_db: EmployeDB) -> EmployeResponse:
        company_name = employe_db.entreprise.nom if employe_db.entreprise else None
        return EmployeResponse(
            idEmploye=employe_db.idEmploye,
            nom=employe_db.nom,
            prenom=employe_db.prenom,
            idPoste=employe_db.idPoste,
            email=employe_db.email,
            employeeId=employe_db.employeeId,
            phone_number=employe_db.phone_number,
            role=employe_db.role,
            idGroupe=employe_db.idGroupe,
            company_name=company_name,
            created_at=employe_db.created_at,
            updated_at=employe_db.updated_at,
            message=None
        )