# main.py
import subprocess
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys

from app.core.config import origins
from app.database import SessionLocal
from app.repositories.employe_repository import EmployeRepository

from app.controllers import (
    serveur_controller,
    registration_controller,
    auth_controller,
    entreprise_controller,
    employer_controller,
    empreintes_controller,
    presences_controller,
    groupe_controller,
    poste_controller,
    notification_controller,
    conge_controller,
)
from app.websocket.endpoint_websocket import router_ws
from app.controllers.noftication_envoyer import router_api

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application démarre : exécution des migrations Alembic...")
    try:
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors des migrations Alembic : {e.stderr}")
        raise

    db = SessionLocal()
    try:
        EmployeRepository(db).cleanup_expired_entries()
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des entrées expirées : {e}")
    finally:
        db.close()

    yield
    logger.info("Application s'arrête.")

app = FastAPI(
    title="FingerTrack Registration & Admin API",
    description="API backend multi-étapes pour inscription, gestion employés, empreintes, présences, etc.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(registration_controller.router, prefix="/api/v1/register", tags=["Inscription"])
app.include_router(auth_controller.router, prefix="/api/v1/auth", tags=["Authentification"])
app.include_router(entreprise_controller.router, prefix="/api/v1/entreprises", tags=["Entreprises"])
app.include_router(employer_controller.router, prefix="/api/v1/employes", tags=["Employés"])
app.include_router(notification_controller.router, prefix="/api/v1/notifications", tags=["Notifications"])  # ✅ ici
app.include_router(empreintes_controller.router, prefix="/api/v1/empreintes", tags=["Empreintes"])
app.include_router(presences_controller.router, prefix="/api/v1/presences", tags=["Présences"])
app.include_router(groupe_controller.router, prefix="/api/v1/groupes", tags=["Groupes"])
app.include_router(serveur_controller.router, prefix="/api/v1/server", tags=["Serveur"])
app.include_router(poste_controller.router, prefix="/api/v1/postes", tags=["Postes"])
app.include_router(conge_controller.router, prefix="/api/v1/conges", tags=["Congés"])
app.include_router(router_api, prefix="/api/v1", tags=["Notify"])
app.include_router(router_ws, tags=["WebSocket"])

@app.get("/")
async def read_root():
    return {"message": "Bienvenue sur l'API FingerTrack"}
