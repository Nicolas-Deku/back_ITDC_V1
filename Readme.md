# Backend FastAPI BioTrack
Ce dépôt contient le code du backend de l'application BioTrack, développé avec FastAPI. Il gère les processus d'inscription multi-étapes (utilisateur et entreprise), l'authentification (par mot de passe et par code), et est conçu pour interagir avec une base de données PostgreSQL.

## Table des matières
#### Prérequis

#### Structure du Projet

#### Configuration de l'Environnement

#### Installation de PostgreSQL

#### Création de la Base de Données et de l'Utilisateur

#### Configuration des Variables d'Environnement

#### Installation des Dépendances Python

#### Création des Tables de la Base de Données

#### Lancement de l'Application

#### Documentation de l'API

## 1. Prérequis
Avant de commencer, assurez-vous d'avoir les éléments suivants installés sur votre système :

Python 3.8+ (recommandé)

pip (gestionnaire de paquets Python)

PostgreSQL (serveur de base de données)

## 2. Structure du Projet
Le projet suit une architecture Modèle-Contrôleur-Service-Repository (MCSR) pour une meilleure organisation et maintenabilité :

backend_fastapi/

    ├── venv/                           # Environnement virtuel Python

    ├── main.py                         # Point d'entrée principal de l'application FastAPI

    ├── create_db_tables.py             # Script pour créer les tables de la DB

    ├── .env.example                    # Exemple de fichier de variables d'environnement

    └── app/

        ├── __init__.py

        ├── core/

        │   ├── __init__.py

        │   └── config.py               # Configuration globale (CORS, DB, SMTP)

        ├── database.py                 # Configuration SQLAlchemy (engine, session, Base)

        ├── models/

        │   ├── __init__.py

        │   ├── auth_models.py          # Modèles Pydantic pour l'authentification

        │   ├── user_models.py          # Modèles Pydantic pour les utilisateurs et l'inscription

        │   └── db_models.py            # Modèles SQLAlchemy pour les tables de la DB

        ├── repositories/

        │   ├── __init__.py

        │   └── user_repository.py      # Gère l'accès aux données (PostgreSQL)

        ├── services/

        │   ├── __init__.py

        │   ├── auth_service.py         # Logique métier pour l'authentification

        │   └── registration_service.py # Logique métier pour l'inscription

        ├── controllers/

        │   ├── __init__.py

        │   ├── auth_controller.py      # Contrôleur pour les endpoints de connexion

        │   └── registration_controller.py # Contrôleur pour les endpoints d'inscription

        └── utils/

            ├── __init__.py

            └── email_sender.py         # Utilitaire pour l'envoi d'e-mails

## 3. Configuration de l'Environnement
Installation de PostgreSQL
Pour les systèmes Linux (Debian/Ubuntu/Mint)
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl status postgresql # Vérifier le statut

Pour les systèmes Windows
Téléchargez l'installateur depuis PostgreSQL Downloads.

Exécutez l'installateur et suivez les instructions. Notez le mot de passe de l'utilisateur postgres que vous définissez.

Création de la Base de Données et de l'Utilisateur
Pour les systèmes Linux
Connectez-vous en tant qu'utilisateur postgres :

sudo -i -u postgres

Accédez au shell psql :

psql

Exécutez les commandes SQL suivantes (remplacez votre_mot_de_passe_secure par un mot de passe fort) :

CREATE USER biotrack_user WITH PASSWORD 'votre_mot_de_passe_secure';
CREATE DATABASE biotrack_db OWNER biotrack_user;
GRANT ALL PRIVILEGES ON DATABASE biotrack_db TO biotrack_user;
\q

Quittez l'utilisateur postgres :

exit

Pour les systèmes Windows
Utilisez pgAdmin (installé avec PostgreSQL) ou le client psql via l'invite de commande.

Via pgAdmin (recommandé) :

Lancez pgAdmin, connectez-vous au serveur postgres.

Créez une nouvelle base de données nommée biotrack_db.

Créez un nouveau rôle de connexion/groupe nommé biotrack_user avec un mot de passe fort.

Changez le propriétaire de la base de données biotrack_db pour biotrack_user.

Via psql (ligne de commande) :

Ouvrez l'invite de commande et naviguez vers le répertoire bin de votre installation PostgreSQL (ex: cd "C:\Program Files\PostgreSQL\16\bin").

Connectez-vous en tant qu'utilisateur postgres : psql -U postgres (entrez le mot de passe de postgres).

Exécutez les mêmes commandes SQL que pour Linux.

Configuration des Variables d'Environnement
Créez un fichier nommé .env à la racine de votre dossier backend_fastapi. Ne committez jamais ce fichier sur Git !

Copiez le contenu de .env.example (que vous devrez créer à la racine du projet) et remplissez-le avec vos informations :

.env:

##### Configuration de la base de données PostgreSQL
DB_USER="biotrack_user"
DB_PASSWORD="votre_mot_de_passe_secure" # Utilisez le mot de passe que vous avez défini
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="biotrack_db"

##### Configuration pour l'envoi d'emails SMTP
##### Pour Gmail, vous devrez générer un "mot de passe d'application"
##### (Activez la validation en deux étapes sur votre compte Google, puis allez dans Sécurité -> Mots de passe d'application)
SMTP_SERVER="smtp.gmail.com" # Ou votre serveur SMTP (ex: smtp.mailgun.org)
SMTP_PORT="587"              # Port standard pour TLS/STARTTLS (pour SMTPS, utilisez 465)
EMAIL_USERNAME="votre_email@gmail.com" # Votre adresse email d'envoi
EMAIL_PASSWORD="votre_mot_de_passe_app" # Votre mot de passe d'application ou mot de passe réel

## 4. Installation des Dépendances Python
Naviguez vers le dossier backend_fastapi :

cd path/to/your/backend_fastapi

Créez un environnement virtuel (si ce n'est pas déjà fait) :

python3 -m venv venv

Activez l'environnement virtuel :

Linux/macOS : source venv/bin/activate

Windows (CMD) : venv\Scripts\activate.bat

Windows (PowerShell) : .\venv\Scripts\Activate.ps1

Installez les dépendances :

pip install fastapi "uvicorn[standard]" sqlalchemy psycopg2-binary python-dotenv
pip install pydantic[email] # Pour la validation des emails

## 5. Création des Tables de la Base de Données
Une fois PostgreSQL configuré et les dépendances installées, exécutez ce script pour créer les tables dans votre base de données :

Assurez-vous d'être dans le dossier backend_fastapi et que l'environnement virtuel est activé.

Exécutez le script :

python create_db_tables.py

Vous devriez voir un message indiquant que les tables ont été créées avec succès.

## 6. Lancement de l'Application
Pour lancer le serveur FastAPI :

Assurez-vous d'être dans le dossier backend_fastapi et que l'environnement virtuel est activé.

Exécutez la commande :

uvicorn main:app --reload --host 0.0.0.0 --port 8000

--reload : Redémarre le serveur automatiquement lors des modifications de code.

--host 0.0.0.0 : Rend le serveur accessible depuis d'autres appareils sur votre réseau local (utilisez 127.0.0.1 si vous ne voulez qu'un accès local).

--port 8000 : Le port sur lequel l'API sera accessible.

## 7. Documentation de l'API
Une fois l'application lancée, vous pouvez accéder à la documentation interactive de l'API :

Swagger UI (pour tester les endpoints) : http://127.0.0.1:8000/docs

ReDoc (pour une vue de la documentation) : http://127.0.0.1:8000/redoc