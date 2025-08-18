from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
import json
import logging
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import exists

from app.models import (
    EmployeDB,
    GroupeDB,
    PosteDB,
    ConfigurationHoraireDB,
    PresenceDB,
    PendingRegistrationDB,
    VerificationCodeDB,
    EmpreinteDB,
)

logger = logging.getLogger(__name__)

class EmployeRepository:
    def __init__(self, db: Session):
        self.db = db
        logger.info(f"Initialisation de EmployeRepository avec db de type {type(self.db)}")

    def get_employe_by_email(self, email: str) -> Optional[EmployeDB]:
        try:
            return self.db.query(EmployeDB).filter(EmployeDB.email == email.lower()).first()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'employé par email {email}: {e}")
            raise

    def get_employe_by_employee_id(self, employee_id: str) -> Optional[EmployeDB]:
        try:
            return self.db.query(EmployeDB).filter(EmployeDB.employeeId == employee_id).first()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'employé par employeeId {employee_id}: {e}")
            raise

    def get_employe_by_id(self, id_employe: UUID) -> Optional[EmployeDB]:
        try:
            return self.db.query(EmployeDB).filter(EmployeDB.idEmploye == id_employe).first()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'employé par ID {id_employe}: {e}")
            raise

    def get_groupe_by_id(self, id_groupe: UUID) -> Optional[GroupeDB]:
        try:
            return self.db.query(GroupeDB).filter(GroupeDB.idGroupe == id_groupe).first()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du groupe par ID {id_groupe}: {e}")
            raise
    def get_poste_by_id(self, id_poste: UUID) -> Optional[PosteDB]:
        try:
            return self.db.query(PosteDB).filter(PosteDB.idPoste == id_poste).first()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du poste par ID {id_poste}: {e}")
            raise
        
    def create_employe(self, employe: EmployeDB) -> EmployeDB:
        try:
            self.db.add(employe)
            self.db.commit()
            self.db.refresh(employe)
            return employe
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Erreur d'intégrité lors de la création de l'employé: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création de l'employé: {e}")
            raise

    def update_employe(self, employe: EmployeDB, update_data: Dict) -> EmployeDB:
        try:
            for key, value in update_data.items():
                setattr(employe, key, value)
            self.db.commit()
            self.db.refresh(employe)
            return employe
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la mise à jour de l'employé {employe.idEmploye}: {e}")
            raise

    def delete_employe(self, employe: EmployeDB) -> None:
        try:
            self.db.delete(employe)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la suppression de l'employé {employe.idEmploye}: {e}")
            raise

    def get_all_employes(self, skip: int = 0, limit: int = 100) -> List[EmployeDB]:
        try:
            return self.db.query(EmployeDB).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des employés : {e}")
            raise

    def add_pending_registration(self, user_email: str, personal_info: Dict, expires_at: datetime):
        try:
            existing = self.db.query(PendingRegistrationDB).filter(PendingRegistrationDB.user_email == user_email.lower()).first()
            if existing:
                existing.personal_info_json = json.dumps(personal_info)
                existing.expires_at = expires_at
            else:
                new_pending = PendingRegistrationDB(
                    id=uuid4(),
                    user_email=user_email.lower(),
                    personal_info_json=json.dumps(personal_info),
                    expires_at=expires_at
                )
                self.db.add(new_pending)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la gestion de la registration en attente pour {user_email}: {e}")
            raise

    def get_pending_registration(self, user_email: str) -> Optional[Dict]:
        try:
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            pending = self.db.query(PendingRegistrationDB).filter(PendingRegistrationDB.user_email == user_email.lower()).first()
            if pending and pending.expires_at > now:
                return {
                    "personal_info_json": json.loads(pending.personal_info_json) if pending.personal_info_json else None,
                    "company_info_json": json.loads(pending.company_info_json) if pending.company_info_json else None,
                    "role_assigned": pending.role_assigned,
                    "expires_at": pending.expires_at,
                }
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la registration en attente pour {user_email}: {e}")
            raise

    def update_pending_registration(self, user_email: str, key: str, value):
        try:
            pending = self.db.query(PendingRegistrationDB).filter(PendingRegistrationDB.user_email == user_email.lower()).first()
            if not pending:
                raise ValueError(f"Aucune registration en attente pour {user_email}")
            if key == "personal_info":
                pending.personal_info_json = json.dumps(value)
            elif key == "company_info":
                pending.company_info_json = json.dumps(value)
            elif key == "role_assigned":
                pending.role_assigned = value
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la mise à jour de la registration en attente pour {user_email}: {e}")
            raise

    def delete_pending_registration(self, user_email: str):
        try:
            self.db.query(PendingRegistrationDB).filter(PendingRegistrationDB.user_email == user_email.lower()).delete()
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la suppression de la registration en attente pour {user_email}: {e}")
            raise

    def set_verification_code(self, email: str, code: str, expires_in_minutes: int):
        try:
            expires_at = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(minutes=expires_in_minutes)
            identifier = email.lower()
            existing_code = self.db.query(VerificationCodeDB).filter(VerificationCodeDB.identifier == identifier).first()
            if existing_code:
                existing_code.code = code
                existing_code.expires_at = expires_at
                self.db.commit()
            else:
                new_code = VerificationCodeDB(identifier=identifier, code=code, expires_at=expires_at)
                self.db.add(new_code)
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la gestion du code de vérification pour {email}: {e}")
            raise

    def get_verification_code(self, email: str) -> Optional[str]:
        try:
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            code_entry = self.db.query(VerificationCodeDB).filter(VerificationCodeDB.identifier == email.lower()).first()
            if code_entry and code_entry.expires_at > now:
                return code_entry.code
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du code de vérification pour {email}: {e}")
            raise

    def delete_verification_code(self, email: str):
        try:
            self.db.query(VerificationCodeDB).filter(VerificationCodeDB.identifier == email.lower()).delete()
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la suppression du code de vérification pour {email}: {e}")
            raise

    def get_employes_by_entreprise(self, idEntreprise: UUID, skip: int = 0, limit: int = 100) -> List[EmployeDB]:
        try:
            return (
                self.db.query(EmployeDB)
                .filter(EmployeDB.idEntreprise == idEntreprise)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            # log error or raise
            raise
    
    def cleanup_expired_entries(self):
        try:
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            self.db.query(PendingRegistrationDB).filter(PendingRegistrationDB.expires_at < now).delete()
            self.db.query(VerificationCodeDB).filter(VerificationCodeDB.expires_at < now).delete()
            self.db.commit()
            logger.info("Nettoyage des entrées expirées effectué avec succès")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors du nettoyage des entrées expirées: {e}")
            raise
    
    def get_employe_by_phone_number(self, phone_number: str) -> Optional[EmployeDB]:
        """
        Retourne l'employé ayant ce numéro de téléphone, ou None s'il n'existe pas.
        """
        try:
            return self.db.query(EmployeDB).filter(EmployeDB.phone_number == phone_number).first()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'employé par numéro de téléphone {phone_number}: {e}")
            raise

    def get_employees_without_fingerprint(self, idEntreprise: UUID) -> List[EmployeDB]:
        """
        Renvoie tous les employés d'une entreprise qui n'ont pas encore
        d'empreinte digitale enregistrée.
        """
        # Sous‑requête EXISTS : il existe une empreinte liée à cet employé
        empreinte_exists = (
            self.db.query(EmpreinteDB.idEmpreinte)
            .filter(EmpreinteDB.idEmploye == EmployeDB.idEmploye)
            .exists()
        )

        # Requête principale : employés dont AUCUNE empreinte n'existe
        return (
            self.db.query(EmployeDB)
            .filter(EmployeDB.idEntreprise == idEntreprise)
            .filter(~empreinte_exists)  # NOT EXISTS(...)
            .options(joinedload(EmployeDB.groupe))  # précharger le groupe
            .all()
        )