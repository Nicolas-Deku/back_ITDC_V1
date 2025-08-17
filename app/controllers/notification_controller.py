from fastapi import APIRouter, Depends, HTTPException
from typing import List
import logging
from app.schemas.schemas import Notification
from app.services.employe_service import EmployeService
from app.api.deps import get_current_active_manager_or_admin, get_employe_service
from app.models import EmployeDB
from datetime import datetime, timezone  # <-- ajout de timezone

router = APIRouter(tags=["Notifications"])
logger = logging.getLogger(__name__)

@router.get(
    "/notif",
    response_model=List[Notification],
    summary="Lister toutes les notifications en attente (pull initial)",
    dependencies=[Depends(get_current_active_manager_or_admin)]
)
async def get_pending_notifications(
    current_user: EmployeDB = Depends(get_current_active_manager_or_admin),
    employe_service: EmployeService = Depends(get_employe_service)
):
    logger.info("[notifications] --- Récupération notifications initiales ---")

    if not current_user.idEntreprise:
        raise HTTPException(
            status_code=400,
            detail="Entreprise non définie pour l'utilisateur."
        )

    notifications = await employe_service.get_pending_fingerprint_notifications(
        current_user=current_user,
        entreprise_id=current_user.idEntreprise
    )

    # Ajouter une date si elle n'existe pas déjà (timezone-aware UTC)
    for notif in notifications:
        if not getattr(notif, "created_at", None):
            notif.created_at = datetime.now(timezone.utc)  # ✅ remplace utcnow()

    return notifications
