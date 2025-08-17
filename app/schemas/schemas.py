from pydantic import BaseModel, EmailStr, Field, UUID4, validator
from typing import Optional, List
from datetime import datetime, time
from app.models import ShiftType


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    sub: str
    email: EmailStr
    idEmploye: str
    employee_id: str
    company_id: Optional[str] = None
    company: Optional[str] = None
    role: str
    idGroupe: Optional[UUID4] = None

    class Config:
        extra = "forbid"


class TokenData(BaseModel):
    sub: str
    email: EmailStr
    idEmploye: str
    employee_id: str
    company_id: Optional[str] = None
    company: Optional[str] = None
    role: str
    idGroupe: Optional[UUID4] = None

    class Config:
        extra = "allow"


class GroupeBase(BaseModel):
    nom: str


class GroupeCreate(GroupeBase):
    nom: str


class GroupeUpdate(BaseModel):
    nom: Optional[str] = None


class ConfigurationHoraireBase(BaseModel):
    type_horaire: ShiftType
    heure_debut_entree: time
    heure_fin_entree: time
    heure_debut_sortie: time
    heure_fin_sortie: time
    seuil_retard: int = 0
    jours_conges_annuels: int = 25
    heures_supplementaires_autorisees: bool = False

    @validator("heure_fin_entree")
    def validate_heure_fin_entree(cls, v, values):
        if "heure_debut_entree" in values and v <= values["heure_debut_entree"]:
            raise ValueError("L'heure de fin d'entrée doit être postérieure à l'heure de début d'entrée.")
        return v

    @validator("heure_fin_sortie")
    def validate_heure_fin_sortie(cls, v, values):
        if "heure_debut_sortie" in values and v <= values["heure_debut_sortie"]:
            raise ValueError("L'heure de fin de sortie doit être postérieure à l'heure de début de sortie.")
        return v


class ConfigurationHoraireCreate(ConfigurationHoraireBase):
    idGroupe: UUID4


class ConfigurationHoraireUpdate(BaseModel):
    type_horaire: Optional[ShiftType] = None
    heure_debut_entree: Optional[time] = None
    heure_fin_entree: Optional[time] = None
    heure_debut_sortie: Optional[time] = None
    heure_fin_sortie: Optional[time] = None
    seuil_retard: Optional[int] = None
    jours_conges_annuels: Optional[int] = None
    heures_supplementaires_autorisees: Optional[bool] = None

    @validator("heure_fin_entree")
    def validate_heure_fin_entree(cls, v, values):
        if "heure_debut_entree" in values and values["heure_debut_entree"] is not None and v <= values["heure_debut_entree"]:
            raise ValueError("L'heure de fin d'entrée doit être postérieure à l'heure de début d'entrée.")
        return v

    @validator("heure_fin_sortie")
    def validate_heure_fin_sortie(cls, v, values):
        if "heure_debut_sortie" in values and values["heure_debut_sortie"] is not None and v <= values["heure_debut_sortie"]:
            raise ValueError("L'heure de fin de sortie doit être postérieure à l'heure de début de sortie.")
        return v


class ConfigurationHoraireResponse(ConfigurationHoraireBase):
    idConfigurationHoraire: UUID4
    idGroupe: UUID4

    class Config:
        from_attributes = True


class GroupeResponse(GroupeBase):
    idGroupe: UUID4
    idEntreprise: UUID4
    created_at: datetime
    updated_at: Optional[datetime]
    configurations_horaires: List[ConfigurationHoraireResponse] = []

    class Config:
        from_attributes = True


class EmployeBase(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    employeeId: str
    phone_number: Optional[str] = None
    idPoste: Optional[UUID4] = None


class EmployeCreate(EmployeBase):
    motDePasse: Optional[str] = None
    role: str = "employee"
    companyName: Optional[str] = None
    companyContactEmail: Optional[EmailStr] = None
    idEntreprise: Optional[UUID4] = None
    idGroupe: Optional[UUID4] = None
    idPoste: Optional[UUID4] = None

    class Config:
        extra = "forbid"


class EmployeUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[EmailStr] = None
    motDePasse: Optional[str] = None
    role: Optional[str] = None
    employeeId: Optional[str] = None
    phone_number: Optional[str] = None
    idEntreprise: Optional[UUID4] = None
    idGroupe: Optional[UUID4] = None
    idPoste: Optional[UUID4] = None

    class Config:
        extra = "forbid"


class EmployeResponse(EmployeBase):
    idEmploye: UUID4
    role: str
    company_name: Optional[str] = None
    idGroupe: Optional[UUID4] = None
    idPoste: Optional[UUID4] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    message: Optional[str] = None
    expires_at: Optional[str] = None

    class Config:
        from_attributes = True


class EntrepriseCreate(BaseModel):
    nom: str
    adresse: Optional[str] = None
    contact_email: Optional[EmailStr] = None

    class Config:
        extra = "allow"


class EntrepriseResponse(BaseModel):
    idEntreprise: UUID4
    nom: str
    adresse: Optional[str]
    contact_email: Optional[EmailStr]
    groupes: List[GroupeResponse] = []
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class EntrepriseUpdate(BaseModel):
    nom: Optional[str] = None
    adresse: Optional[str] = None
    contact_email: Optional[EmailStr] = None

    class Config:
        extra = "forbid"


class EmpreinteCreate(BaseModel):
    idEmploye: UUID4
    donneesBiometriques: bytes
    appareil_id: Optional[str] = None

    @validator("donneesBiometriques")
    def validate_donnees_biometriques(cls, v):
        if not v:
            raise ValueError("Les données biométriques ne peuvent pas être vides.")
        return v

    class Config:
        extra = "forbid"


class EmpreinteResponse(BaseModel):
    idEmpreinte: UUID4
    idEmploye: UUID4
    appareil_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PresenceCreate(BaseModel):
    idEmploye: UUID4
    type: str = Field(..., pattern="^(entree|sortie)$")
    timestamp: datetime
    methode: str = Field(..., pattern="^(biometrique|code_pin|carte_rfid)$")
    appareil_id: Optional[str] = None
    notes: Optional[str] = None
    idConfigurationHoraire: Optional[UUID4] = None

    class Config:
        extra = "forbid"


class PresenceResponse(BaseModel):
    idPresence: UUID4
    idEmploye: UUID4
    type: str
    timestamp: datetime
    methode: str
    appareil_id: Optional[str] = None
    notes: Optional[str] = None
    idConfigurationHoraire: Optional[UUID4] = None
    statut: str

    class Config:
        from_attributes = True


class FingerprintScanRequest(BaseModel):
    idEmploye: UUID4
    donneesBiometriques: bytes
    appareil_id: Optional[str] = None
    idConfigurationHoraire: Optional[UUID4] = None

    class Config:
        extra = "forbid"


class MessageResponse(BaseModel):
    message: str
    expires_at: Optional[str] = None  # Peut contenir une date ISO


class PersonalInfo(BaseModel):
    userEmail: EmailStr
    lastName: str
    firstName: str
    position: Optional[str] = None
    employeeId: str
    phoneNumber: Optional[str] = None
    password: Optional[str] = None 

    class Config:
        extra = "forbid"


class UserVerification(BaseModel):
    email: EmailStr
    code: str

    class Config:
        extra = "forbid"


class CompanyInfo(BaseModel):
    companyName: str
    companyContactEmail: EmailStr
    adresse: Optional[str] = None

    class Config:
        extra = "forbid"


class CompanyVerification(BaseModel):
    userEmail: EmailStr
    companyCode: str

    class Config:
        extra = "forbid"


class FinalRegistrationData(BaseModel):
    lastName: str
    firstName: str
    employeeId: str
    userEmail: EmailStr
    position: Optional[str] = None
    phoneNumber: Optional[str] = None
    password: Optional[str] = None
    companyName: str
    companyContactEmail: EmailStr
    idGroupe: Optional[UUID4] = None
    adresse: Optional[str] = None  # Champ pour adresse entreprise lors de l’enregistrement

    class Config:
        extra = "forbid"


class SendCodeRequest(BaseModel):
    type: str = Field(..., pattern="^(email|sms)$")
    identifier: str

    class Config:
        extra = "forbid"


class VerifyCodeRequest(BaseModel):
    type: str = Field(..., pattern="^(email|sms)$")
    identifier: str
    code: str

    class Config:
        extra = "forbid"


class LoginCredentials(BaseModel):
    email: EmailStr
    password: str

    class Config:
        extra = "forbid"


class CongeBase(BaseModel):
    idEmploye: UUID4
    type_conge: str
    date_debut: datetime
    date_fin: datetime
    statut: str = "en_attente"
    commentaire: Optional[str] = None


class CongeCreate(CongeBase):
    pass


class CongeUpdate(BaseModel):
    type_conge: Optional[str] = None
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    statut: Optional[str] = None
    commentaire: Optional[str] = None
    approuve_par: Optional[UUID4] = None


class CongeResponse(CongeBase):
    idConge: UUID4
    approuve_par: Optional[UUID4] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    idEmploye: UUID4
    access_token: str
    token_type: str = "bearer"
    date_expiration: datetime
    is_active: bool = True


class SessionCreate(SessionBase):
    pass


class SessionResponse(SessionBase):
    idSession: UUID4
    date_creation: datetime

    class Config:
        from_attributes = True

class PosteBase(BaseModel):
    nom: str  # nom non vide
    description: Optional[str] = None
    idEntreprise: UUID4  # FK vers l'entreprise


class PosteCreate(PosteBase):
    # ici on hérite et on peut ajouter validations spécifiques si besoin
    class Config:
        extra = "forbid"


class PosteUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None

    class Config:
        extra = "forbid"

class Notification(BaseModel):
    id: UUID4
    idEmploye: UUID4
    employeeName: Optional[str] = None
    department: Optional[str] = None
    message: Optional[str] = None
    idEntreprise: UUID4 | None = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PosteResponse(PosteBase):
    idPoste: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True