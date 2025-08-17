# alembic/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 🔹 Import de la base et des modèles AVANT de définir target_metadata
from app.database import Base

# Importer explicitement tous les modèles pour que Alembic les détecte
from app.models import (
    EntrepriseDB,
    GroupeDB,
    ConfigurationHoraireDB,
    EmployeDB,
    EmpreinteDB,
    PresenceDB,
    CongeDB,
    SessionDB,
    PendingRegistrationDB,
    VerificationCodeDB,
    PosteDB
)

# Charger la configuration Alembic
config = context.config
fileConfig(config.config_file_name)

# 🔹 Lier les métadonnées
target_metadata = Base.metadata

# 🔹 Debug : afficher les tables détectées
print("Tables détectées par Alembic :", list(target_metadata.tables.keys()))

def run_migrations_offline():
    """Exécuter les migrations en mode 'offline'."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Exécuter les migrations en mode 'online'."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
