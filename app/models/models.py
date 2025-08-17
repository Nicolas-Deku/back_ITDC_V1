from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Time, Integer, Boolean, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid
from enum import Enum as PyEnum
from app.database import Base


class ShiftType(PyEnum):
    MATIN = "matin"
    APRES_MIDI = "apres-midi"
    SOIR = "nuit"
    SUPPLEMENTAIRE = "personnaliser"

class PosteDB(Base):
    __tablename__ = "poste"

    idPoste = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nom = Column(String, nullable=False)  # Nom du poste (ex : "Développeur", "Commercial")
    description = Column(String, nullable=True)  # Description optionnelle du poste
    idEntreprise = Column(UUID(as_uuid=True), ForeignKey("entreprise.idEntreprise", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    entreprise = relationship("EntrepriseDB", back_populates="postes")
    employes = relationship("EmployeDB", back_populates="poste")

# --- Modification de EntrepriseDB pour ajouter la relation postes ---

class EntrepriseDB(Base):
    __tablename__ = "entreprise"
    idEntreprise = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nom = Column(String, nullable=False, unique=True)
    adresse = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    employes = relationship("EmployeDB", back_populates="entreprise", cascade="all, delete-orphan")
    groupes = relationship("GroupeDB", back_populates="entreprise", cascade="all, delete-orphan")

    postes = relationship(
        "PosteDB",
        back_populates="entreprise",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
# --- Modification de EmployeDB pour référencer PosteDB ---

class EmployeDB(Base):
    __tablename__ = "employe"
    idEmploye = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)

    # Suppression de l'ancien champ 'poste' (string)
    # poste = Column(String, nullable=True)

    email = Column(String, nullable=False, unique=True, index=True)
    motDePasse = Column(String, nullable=False)
    role = Column(String, nullable=False, default="employee")
    employeeId = Column(String, nullable=False, unique=True, index=True)
    phone_number = Column(String, nullable=True, unique=True)
    idEntreprise = Column(UUID(as_uuid=True), ForeignKey("entreprise.idEntreprise"), nullable=False)
    idGroupe = Column(UUID(as_uuid=True), ForeignKey("groupe.idGroupe"), nullable=True)

    # Nouveau champ connexion avec PosteDB (FK)
    idPoste = Column(UUID(as_uuid=True), ForeignKey("poste.idPoste"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    empreintes = relationship("EmpreinteDB", back_populates="employe", cascade="all, delete-orphan")
    presences = relationship("PresenceDB", back_populates="employe", cascade="all, delete-orphan")
    conges = relationship("CongeDB", foreign_keys="CongeDB.idEmploye", back_populates="employe", cascade="all, delete-orphan")
    sessions = relationship("SessionDB", back_populates="employe", cascade="all, delete-orphan")

    entreprise = relationship("EntrepriseDB", back_populates="employes")
    groupe = relationship("GroupeDB", back_populates="employes")

    poste = relationship("PosteDB", back_populates="employes")
    
class GroupeDB(Base):
    __tablename__ = "groupe"
    idGroupe = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nom = Column(String, nullable=False)
    idEntreprise = Column(UUID(as_uuid=True), ForeignKey("entreprise.idEntreprise"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    entreprise = relationship("EntrepriseDB", back_populates="groupes")
    employes = relationship("EmployeDB", back_populates="groupe")
    configurations_horaires = relationship("ConfigurationHoraireDB", back_populates="groupe", cascade="all, delete-orphan")

class ConfigurationHoraireDB(Base):
    __tablename__ = "configuration_horaire"
    idConfigurationHoraire = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idGroupe = Column(UUID(as_uuid=True), ForeignKey("groupe.idGroupe"), nullable=False)
    type_horaire = Column(Enum(ShiftType), nullable=False)
    heure_debut_entree = Column(Time, nullable=False)
    heure_fin_entree = Column(Time, nullable=False)
    heure_debut_sortie = Column(Time, nullable=False)
    heure_fin_sortie = Column(Time, nullable=False)
    seuil_retard = Column(Integer, nullable=False, default=0)
    jours_conges_annuels = Column(Integer, nullable=False, default=25)
    heures_supplementaires_autorisees = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    groupe = relationship("GroupeDB", back_populates="configurations_horaires")
    presences = relationship("PresenceDB", back_populates="configuration_horaire")


class EmpreinteDB(Base):
    __tablename__ = "empreinte"
    idEmpreinte = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idEmploye = Column(UUID(as_uuid=True), ForeignKey("employe.idEmploye"), nullable=False)
    donneesBiometriques = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    employe = relationship("EmployeDB", back_populates="empreintes")

class PresenceDB(Base):
    __tablename__ = "presence"
    idPresence = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idEmploye = Column(UUID(as_uuid=True), ForeignKey("employe.idEmploye"), nullable=False)
    type = Column(String, default="CHECK_IN", nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    methode = Column(String, default="fingerprint", nullable=False)
    appareil_id = Column(String, nullable=True)
    statut = Column(String, default="valide", nullable=False)
    notes = Column(String, nullable=True)
    idConfigurationHoraire = Column(UUID(as_uuid=True), ForeignKey("configuration_horaire.idConfigurationHoraire"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    employe = relationship("EmployeDB", back_populates="presences")
    configuration_horaire = relationship("ConfigurationHoraireDB", back_populates="presences")

class CongeDB(Base):
    __tablename__ = "conge"
    idConge = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idEmploye = Column(UUID(as_uuid=True), ForeignKey("employe.idEmploye"), nullable=False)
    type_conge = Column(String, nullable=False, default="paye")
    date_debut = Column(DateTime(timezone=True), nullable=False)
    date_fin = Column(DateTime(timezone=True), nullable=False)
    statut = Column(String, nullable=False, default="en_attente")
    commentaire = Column(String, nullable=True)
    approuve_par = Column(UUID(as_uuid=True), ForeignKey("employe.idEmploye"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    employe = relationship("EmployeDB", foreign_keys=[idEmploye], back_populates="conges")
    approbateur = relationship("EmployeDB", foreign_keys=[approuve_par])

class SessionDB(Base):
    __tablename__ = "session"
    idSession = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idEmploye = Column(UUID(as_uuid=True), ForeignKey("employe.idEmploye"), nullable=False)
    access_token = Column(String, nullable=False, unique=True)
    token_type = Column(String, nullable=False, default="bearer")
    date_creation = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_expiration = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    employe = relationship("EmployeDB", back_populates="sessions")

class PendingRegistrationDB(Base):
    __tablename__ = "pending_registration"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_email = Column(String, nullable=False, unique=True, index=True)
    personal_info_json = Column(String, nullable=True)
    company_info_json = Column(String, nullable=True)
    role_assigned = Column(String, nullable=True, default="employee")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

class VerificationCodeDB(Base):
    __tablename__ = "verification_code"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier = Column(String, nullable=False, unique=True, index=True)
    code = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)