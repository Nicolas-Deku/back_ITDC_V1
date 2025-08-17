from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from uuid import UUID
import logging

from app.models import GroupeDB, ConfigurationHoraireDB, EntrepriseDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroupeRepository:
    """
    Gère les opérations de persistance des données pour les groupes et les configurations horaires.
    """
    def __init__(self, db: Session):
        self.db = db

    def create_groupe(self, groupe_data: Dict, entreprise: EntrepriseDB) -> GroupeDB:
        """
        Crée un nouveau groupe pour une entreprise.
        """
        db_groupe = GroupeDB(
            nom=groupe_data["nom"],
            idEntreprise=entreprise.idEntreprise
        )
        self.db.add(db_groupe)
        self.db.commit()
        self.db.refresh(db_groupe)
        logger.info(f"Groupe créé : {db_groupe.nom} pour entreprise {entreprise.nom}")
        return db_groupe

    def get_groupe_by_id(self, groupe_id: UUID) -> Optional[GroupeDB]:
        """
        Récupère un groupe par son ID.
        """
        return self.db.query(GroupeDB).filter(GroupeDB.idGroupe == groupe_id).first()

    def get_groupes_by_entreprise(self, entreprise_id: UUID) -> List[GroupeDB]:
        """
        Liste tous les groupes d'une entreprise.
        """
        return self.db.query(GroupeDB).filter(GroupeDB.idEntreprise == entreprise_id).all()

    def update_groupe(self, groupe: GroupeDB, update_data: Dict) -> GroupeDB:
        """
        Met à jour un groupe existant.
        """
        for field, value in update_data.items():
            if hasattr(groupe, field):
                setattr(groupe, field, value)
        self.db.commit()
        self.db.refresh(groupe)
        logger.info(f"Groupe mis à jour : {groupe.nom}")
        return groupe

    def delete_groupe(self, groupe: GroupeDB):
        """
        Supprime un groupe.
        """
        self.db.delete(groupe)
        self.db.commit()
        logger.info(f"Groupe supprimé : {groupe.nom}")

    def create_configuration_horaire(self, config_data: Dict, groupe: GroupeDB) -> ConfigurationHoraireDB:
        """
        Crée une configuration horaire pour un groupe.
        """
        db_config = ConfigurationHoraireDB(
            idGroupe=groupe.idGroupe,
            type_horaire=config_data["type_horaire"],
            heure_debut_entree=config_data["heure_debut_entree"],
            heure_fin_entree=config_data["heure_fin_entree"],
            heure_debut_sortie=config_data["heure_debut_sortie"],
            heure_fin_sortie=config_data["heure_fin_sortie"],
            seuil_retard=config_data.get("seuil_retard", 0),
            jours_conges_annuels=config_data.get("jours_conges_annuels", 25),
            heures_supplementaires_autorisees=config_data.get("heures_supplementaires_autorisees", False)
        )
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        logger.info(f"Configuration horaire créée pour groupe {groupe.idGroupe} avec type_horaire {db_config.type_horaire}")
        return db_config

    def get_configurations_horaires_by_groupe(self, groupe_id: UUID) -> List[ConfigurationHoraireDB]:
        """
        Récupère toutes les configurations horaires d'un groupe.
        """
        return self.db.query(ConfigurationHoraireDB).filter(ConfigurationHoraireDB.idGroupe == groupe_id).all()

    def get_configuration_horaire_by_id(self, config_id: UUID) -> Optional[ConfigurationHoraireDB]:
        """
        Récupère une configuration horaire par son ID.
        """
        return self.db.query(ConfigurationHoraireDB).filter(ConfigurationHoraireDB.idConfigurationHoraire == config_id).first()

    def update_configuration_horaire(self, config: ConfigurationHoraireDB, update_data: Dict) -> ConfigurationHoraireDB:
        """
        Met à jour une configuration horaire existante.
        """
        for field, value in update_data.items():
            if hasattr(config, field):
                setattr(config, field, value)
        self.db.commit()
        self.db.refresh(config)
        logger.info(f"Configuration horaire mise à jour pour groupe {config.idGroupe}")
        return config

    def delete_configuration_horaire(self, config: ConfigurationHoraireDB):
        """
        Supprime une configuration horaire.
        """
        self.db.delete(config)
        self.db.commit()
        logger.info(f"Configuration horaire supprimée pour groupe {config.idGroupe}")

    def get_entreprise_by_id(self, entreprise_id: UUID) -> Optional[EntrepriseDB]:
        """
        Récupère une entreprise par son ID.
        """
        return self.db.query(EntrepriseDB).filter(EntrepriseDB.idEntreprise == entreprise_id).first()