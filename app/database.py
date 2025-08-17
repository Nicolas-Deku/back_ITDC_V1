from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import DATABASE_URL
import logging
from sqlalchemy import text


# Configurer la journalisation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vérifier que DATABASE_URL est défini
if not DATABASE_URL:
    logger.error("DATABASE_URL n'est pas défini dans la configuration")
    raise ValueError("DATABASE_URL doit être défini dans app.core.config")

# Créer le moteur SQLAlchemy
try:
    engine = create_engine(DATABASE_URL, echo=True)  # echo=True pour le débogage
except Exception as e:
    logger.error(f"Erreur lors de la création du moteur SQLAlchemy: {str(e)}")
    raise

# Créer une fabrique de sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles SQLAlchemy
Base = declarative_base()

def get_db():
    """
    Fournit une session de base de données pour chaque requête.
    """
    db = SessionLocal()
    try:
        # Vérifier que la session est valide
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        logger.error(f"Erreur lors de la création de la session de base de données: {str(e)}")
        raise
    finally:
        db.close()