from fastapi import APIRouter, HTTPException
import logging
from app.websocket.websocket import web_notification_manager, desktop_notification_manager
from app.schemas.schemas import Notification
from datetime import datetime, timezone


router_api = APIRouter()
logger = logging.getLogger(__name__)

@router_api.post("/notify")
async def send_notification(notification: Notification):
    try:
        data = notification.model_dump()
        # Ajouter la date d'envoi
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        company_id = str(notification.idEntreprise).lower()

        await web_notification_manager.send_to_company(company_id, "notification", data)
        await desktop_notification_manager.send_to_company(company_id, "notification", data)

        logger.info(f"[WS] Notification envoyée à l'entreprise {company_id}")
        return {"message": "Notification envoyée"}
    except Exception as e:
        logger.error(f"[WS] Erreur envoi notification : {e}")
        raise HTTPException(status_code=500, detail="Erreur d'envoi de la notification")
