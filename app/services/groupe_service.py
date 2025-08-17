from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging
from fastapi import HTTPException, status

from app.models import EmployeDB, GroupeDB, ConfigurationHoraireDB, EntrepriseDB
from app.repositories.groupe_repository import GroupeRepository
from app.schemas.schemas import (
    GroupeCreate, GroupeUpdate, GroupeResponse,
    ConfigurationHoraireCreate, ConfigurationHoraireUpdate, ConfigurationHoraireResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroupeService:
    """
    Gère la logique métier pour les groupes et leurs configurations horaires.
    """
    def __init__(self, db: Session):
        self.repository = GroupeRepository(db)

    def create_groupe(self, groupe_data: GroupeCreate, entreprise_id: UUID, current_user: EmployeDB) -> GroupeResponse:
        """
        Crée un nouveau groupe pour une entreprise.

        Args:
            groupe_data: Données du groupe (nom).
            entreprise_id: ID de l'entreprise.
            current_user: Utilisateur authentifié (doit être admin).

        Returns:
            GroupeResponse: Détails du groupe créé.

        Raises:
            ValueError: Si l'entreprise n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        if current_user.role not in ["admin", "manager"]:
            logger.error(f"Utilisateur {current_user.email} non autorisé à créer un groupe.")
            raise ValueError("Seuls les admins ou managers peuvent créer un groupe.")

        entreprise = self.repository.get_entreprise_by_id(entreprise_id)
        if not entreprise:
            logger.error(f"Entreprise avec ID {entreprise_id} non trouvée.")
            raise ValueError("Entreprise non trouvée.")

        if current_user.idEntreprise != entreprise_id:
            logger.error(f"Utilisateur {current_user.email} n'appartient pas à l'entreprise {entreprise_id}.")
            raise ValueError("Vous n'êtes pas autorisé à créer un groupe pour cette entreprise.")

        groupe_data_dict = groupe_data.dict()
        groupe = self.repository.create_groupe(groupe_data_dict, entreprise)
        logger.info(f"Groupe créé : {groupe.nom} pour l'entreprise {entreprise.nom}")
        return self._map_groupe_to_response(groupe)

    def get_groupe_by_id(self, groupe_id: UUID, current_user: EmployeDB) -> Optional[GroupeResponse]:
        """
        Récupère un groupe par son ID.

        Args:
            groupe_id: ID du groupe.
            current_user: Utilisateur authentifié.

        Returns:
            GroupeResponse: Détails du groupe ou None si non trouvé.
        """
        groupe = self.repository.get_groupe_by_id(groupe_id)
        if not groupe:
            return None
        if current_user.idEntreprise != groupe.idEntreprise:
            logger.error(f"Utilisateur {current_user.email} n'a pas accès au groupe {groupe_id}.")
            raise ValueError("Vous n'êtes pas autorisé à accéder à ce groupe.")
        return self._map_groupe_to_response(groupe)

    def get_groupes_by_entreprise(self, entreprise_id: UUID, current_user: EmployeDB) -> List[GroupeResponse]:
        """
        Liste tous les groupes d'une entreprise.

        Args:
            entreprise_id: ID de l'entreprise.
            current_user: Utilisateur authentifié.

        Returns:
            List[GroupeResponse]: Liste des groupes.

        Raises:
            ValueError: Si l'entreprise n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        entreprise = self.repository.get_entreprise_by_id(entreprise_id)
        if not entreprise:
            logger.error(f"Entreprise avec ID {entreprise_id} non trouvée.")
            raise ValueError("Entreprise non trouvée.")
        if current_user.idEntreprise != entreprise_id:
            logger.error(f"Utilisateur {current_user.email} n'a pas accès à l'entreprise {entreprise_id}.")
            raise ValueError("Vous n'êtes pas autorisé à accéder aux groupes de cette entreprise.")
        groupes = self.repository.get_groupes_by_entreprise(entreprise_id)
        return [self._map_groupe_to_response(g) for g in groupes]

    def update_groupe(self, groupe_id: UUID, groupe_data: GroupeUpdate, current_user: EmployeDB) -> GroupeResponse:
        """
        Met à jour un groupe existant.

        Args:
            groupe_id: ID du groupe.
            groupe_data: Données à mettre à jour.
            current_user: Utilisateur authentifié.

        Returns:
            GroupeResponse: Détails du groupe mis à jour.

        Raises:
            ValueError: Si le groupe n'existe pas ou si l'utilisateur n'a pas les droits.
        """
        groupe = self.repository.get_groupe_by_id(groupe_id)
        if not groupe:
            logger.error(f"Groupe avec ID {groupe_id} non trouvé.")
            raise ValueError("Groupe non trouvé.")
        if current_user.idEntreprise != groupe.idEntreprise:
            logger.error(f"Utilisateur {current_user.email} n'a pas accès au groupe {groupe_id}.")
            raise ValueError("Vous n'êtes pas autorisé à modifier ce groupe.")
        update_data = groupe_data.dict(exclude_unset=True)
        updated_groupe = self.repository.update_groupe(groupe, update_data)
        logger.info(f"Groupe mis à jour : {updated_groupe.nom}")
        return self._map_groupe_to_response(updated_groupe)

    def delete_groupe(self, groupe_id: UUID, current_user: EmployeDB):
        """
        Supprime un groupe s'il n'a pas d'employés associés.

        Args:
            groupe_id: ID du groupe.
            current_user: Utilisateur authentifié.

        Raises:
            ValueError: Si le groupe n'existe pas, contient des employés, ou si l'utilisateur n'a pas les droits.
        """
        groupe = self.repository.get_groupe_by_id(groupe_id)
        if not groupe:
            logger.error(f"Groupe avec ID {groupe_id} non trouvé.")
            raise ValueError("Groupe non trouvé.")
        if current_user.idEntreprise != groupe.idEntreprise:
            logger.error(f"Utilisateur {current_user.email} n'a pas accès au groupe {groupe_id}.")
            raise ValueError("Vous n'êtes pas autorisé à supprimer ce groupe.")
        if groupe.employes:
            logger.error(f"Le groupe {groupe_id} contient des employés et ne peut pas être supprimé.")
            raise ValueError("Le groupe contient des employés et ne peut pas être supprimé.")
        self.repository.delete_groupe(groupe)
        logger.info(f"Groupe supprimé : {groupe.nom}")

    def create_configuration_horaire(self, groupe_id: UUID, config_data: ConfigurationHoraireCreate, current_user: EmployeDB) -> ConfigurationHoraireResponse:
        """
        Crée une configuration horaire pour un groupe.

        Args:
            groupe_id: ID du groupe.
            config_data: Données de la configuration horaire.
            current_user: Utilisateur authentifié.

        Returns:
            ConfigurationHoraireResponse: Détails de la configuration créée.

        Raises:
            ValueError: Si le groupe n'existe pas, il y a déjà deux configurations, ou si l'utilisateur n'a pas les droits.
        """
        groupe = self.repository.get_groupe_by_id(groupe_id)
        if not groupe:
            logger.error(f"Groupe avec ID {groupe_id} non trouvé.")
            raise ValueError("Groupe non trouvé.")
        if current_user.idEntreprise != groupe.idEntreprise:
            logger.error(f"Utilisateur {current_user.email} n'a pas accès au groupe {groupe_id}.")
            raise ValueError("Vous n'êtes pas autorisé à créer une configuration pour ce groupe.")
        existing_configs = self.repository.get_configurations_horaires_by_groupe(groupe_id)
        if len(existing_configs) >= 2:
            logger.error(f"Le groupe {groupe_id} a déjà deux configurations horaires.")
            raise ValueError("Un groupe ne peut avoir que deux configurations horaires maximum.")
        existing_types = [config.type_horaire for config in existing_configs]
        if config_data.type_horaire in existing_types:
            logger.error(f"Le type_horaire {config_data.type_horaire} est déjà utilisé pour le groupe {groupe_id}.")
            raise ValueError(f"Le type_horaire {config_data.type_horaire} est déjà utilisé pour ce groupe.")
        config = self.repository.create_configuration_horaire(config_data.dict(), groupe)
        logger.info(f"Configuration horaire créée pour le groupe {groupe_id} avec type_horaire {config.type_horaire}")
        return self._map_configuration_to_response(config)

    def get_configurations_horaires_by_groupe(self, groupe_id: UUID, current_user: EmployeDB) -> List[ConfigurationHoraireResponse]:
        """
        Récupère les configurations horaires d'un groupe.

        Args:
            groupe_id: ID du groupe.
            current_user: Utilisateur authentifié.

        Returns:
            List[ConfigurationHoraireResponse]: Liste des configurations horaires.
        """
        groupe = self.repository.get_groupe_by_id(groupe_id)
        if not groupe:
            logger.error(f"Groupe avec ID {groupe_id} non trouvé.")
            raise ValueError("Groupe non trouvé.")
        if current_user.idEntreprise != groupe.idEntreprise:
            logger.error(f"Utilisateur {current_user.email} n'a pas accès au groupe {groupe_id}.")
            raise ValueError("Vous n'êtes pas autorisé à accéder aux configurations de ce groupe.")
        configs = self.repository.get_configurations_horaires_by_groupe(groupe_id)
        return [self._map_configuration_to_response(config) for config in configs]

    def update_configuration_horaire(self, config_id: UUID, config_data: ConfigurationHoraireUpdate, current_user: EmployeDB) -> ConfigurationHoraireResponse:
        """
        Met à jour une configuration horaire spécifique.

        Args:
            config_id: ID de la configuration horaire.
            config_data: Données à mettre à jour.
            current_user: Utilisateur authentifié.

        Returns:
            ConfigurationHoraireResponse: Détails de la configuration mise à jour.

        Raises:
            ValueError: Si la configuration ou le groupe n'existe pas.
        """
        config = self.repository.get_configuration_horaire_by_id(config_id)
        if not config:
            logger.error(f"Configuration horaire avec ID {config_id} non trouvée.")
            raise ValueError("Configuration horaire non trouvée.")
        groupe = self.repository.get_groupe_by_id(config.idGroupe)
        if not groupe:
            logger.error(f"Groupe avec ID {config.idGroupe} non trouvé.")
            raise ValueError("Groupe non trouvé.")
        if current_user.idEntreprise != groupe.idEntreprise:
            logger.error(f"Utilisateur {current_user.email} n'a pas accès au groupe {config.idGroupe}.")
            raise ValueError("Vous n'êtes pas autorisé à modifier la configuration de ce groupe.")
        if config_data.type_horaire:
            existing_configs = self.repository.get_configurations_horaires_by_groupe(config.idGroupe)
            existing_types = [c.type_horaire for c in existing_configs if c.idConfigurationHoraire != config_id]
            if config_data.type_horaire in existing_types:
                logger.error(f"Le type_horaire {config_data.type_horaire} est déjà utilisé pour le groupe {config.idGroupe}.")
                raise ValueError(f"Le type_horaire {config_data.type_horaire} est déjà utilisé pour ce groupe.")
        update_data = config_data.dict(exclude_unset=True)
        updated_config = self.repository.update_configuration_horaire(config, update_data)
        logger.info(f"Configuration horaire mise à jour pour le groupe {config.idGroupe}")
        return self._map_configuration_to_response(updated_config)

    def delete_configuration_horaire(self, config_id: UUID, current_user: EmployeDB):
        """
        Supprime une configuration horaire spécifique.

        Args:
            config_id: ID de la configuration horaire à supprimer.
            current_user: Utilisateur authentifié.

        Raises:
            ValueError: Si la configuration ou le groupe n'existe pas,
                        ou s'il ne reste qu'une configuration après suppression.
        """
        config = self.repository.get_configuration_horaire_by_id(config_id)
        if not config:
            logger.error(f"Configuration horaire avec ID {config_id} non trouvée.")
            raise ValueError("Configuration horaire non trouvée.")

        groupe = self.repository.get_groupe_by_id(config.idGroupe)
        if not groupe:
            logger.error(f"Groupe avec ID {config.idGroupe} non trouvé.")
            raise ValueError("Groupe non trouvé.")

        if current_user.idEntreprise != groupe.idEntreprise:
            logger.error(f"Utilisateur {current_user.email} n'a pas accès au groupe {config.idGroupe}.")
            raise ValueError("Vous n'êtes pas autorisé à supprimer la configuration de ce groupe.")

        existing_configs = self.repository.get_configurations_horaires_by_groupe(config.idGroupe)
        if len(existing_configs) <= 1:
            logger.error(f"Le groupe {config.idGroupe} ne peut pas avoir moins d'une configuration horaire.")
            raise ValueError("Un groupe doit avoir au moins une configuration horaire.")

        self.repository.delete_configuration_horaire(config)
        logger.info(f"Configuration horaire supprimée pour le groupe {config.idGroupe}")

    def _map_groupe_to_response(self, groupe: GroupeDB) -> GroupeResponse:
        """
        Mappe un objet GroupeDB à un modèle Pydantic GroupeResponse.
        """
        return GroupeResponse(
            idGroupe=groupe.idGroupe,
            nom=groupe.nom,
            idEntreprise=groupe.idEntreprise,
            configurations_horaires=[self._map_configuration_to_response(config) for config in groupe.configurations_horaires],
            created_at=groupe.created_at,
            updated_at=groupe.updated_at
        )

    def _map_configuration_to_response(self, config: ConfigurationHoraireDB) -> ConfigurationHoraireResponse:
        """
        Mappe un objet ConfigurationHoraireDB à un modèle Pydantic ConfigurationHoraireResponse.
        """
        return ConfigurationHoraireResponse(
            idConfigurationHoraire=config.idConfigurationHoraire,
            idGroupe=config.idGroupe,
            type_horaire=config.type_horaire,
            heure_debut_entree=config.heure_debut_entree,
            heure_fin_entree=config.heure_fin_entree,
            heure_debut_sortie=config.heure_debut_sortie,
            heure_fin_sortie=config.heure_fin_sortie,
            seuil_retard=config.seuil_retard,
            jours_conges_annuels=config.jours_conges_annuels,
            heures_supplementaires_autorisees=config.heures_supplementaires_autorisees
        )