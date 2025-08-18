# app/core/config.py
import os

from dotenv import load_dotenv

# Charge les variables d'environnement du fichier .env
load_dotenv()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost",
    "http://192.168.1.201:5173",
    # Autres URL front si besoin
]


# Paramètres SMTP pour l'envoi d'emails
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "default_sender@example.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "default_password")

# Configuration de la base de données PostgreSQL ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Sinon construire la chaîne à partir des composants
    DB_USER = os.getenv("DB_USER", "biotrack_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "votre_mot_de_passe_secure")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "biotrack_db")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"