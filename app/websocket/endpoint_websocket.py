from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.websocket.websocket import web_notification_manager
from app.core.security import decode_token
import logging

router_ws = APIRouter()
logger = logging.getLogger(__name__)

@router_ws.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = decode_token(token)
        company_id = payload.get("company_id", "").lower()
        logger.info(f"🔍 Validation token WS, company_id={company_id}")  # ✅ Log validation token
        if not company_id:
            logger.warning("⚠️ Pas de company_id dans le token, fermeture WS")
            await websocket.close(code=4401)
            return
    except Exception as e:
        logger.error(f"❌ Erreur validation token WS: {e}")
        await websocket.close(code=4401)
        return

    await web_notification_manager.connect(company_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket déconnecté pour company_id={company_id}")  # ✅ Log déconnexion
        web_notification_manager.disconnect(company_id, websocket)