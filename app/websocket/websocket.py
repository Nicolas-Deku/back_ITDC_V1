from typing import Dict, List
from fastapi import WebSocket
import logging
import json
from uuid import UUID

logger = logging.getLogger(__name__)

def _json_default(obj):
    """
    Convertit les objets non JSON-sérialisables (UUID, datetime, etc.)
    en formats compatibles JSON.
    """
    if isinstance(obj, UUID):
        return str(obj)
    # On peut ajouter d'autres conversions si besoin (datetime → isoformat, Decimal → str, etc.)
    raise TypeError(f"Type {type(obj)} not serializable")

class NotificationManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, company_id: str, websocket: WebSocket):
        await websocket.accept()
        if company_id not in self.active_connections:
            self.active_connections[company_id] = []
        self.active_connections[company_id].append(websocket)
        logger.info(
            f"✅ Nouvelle connexion WS pour company_id={company_id}, "
            f"total={len(self.active_connections[company_id])}"
        )

    def disconnect(self, company_id: str, websocket: WebSocket):
        if company_id in self.active_connections:
            if websocket in self.active_connections[company_id]:
                self.active_connections[company_id].remove(websocket)
                logger.info(
                    f"🔌 Déconnexion WS pour company_id={company_id}, "
                    f"total restant={len(self.active_connections.get(company_id, []))}"
                )
                if not self.active_connections[company_id]:
                    del self.active_connections[company_id]

    async def send_to_company(self, company_id: str, event: str, data: dict):
        logger.info(
            f"📤 Tentative envoi WS à company_id={company_id}, event={event}, data={data}"
        )
        if company_id in self.active_connections:
            disconnected = []
            for ws in list(self.active_connections[company_id]):
                try:
                    payload = {"event": event, "data": data}
                    # ✅ Conversion UUID -> str automatique
                    await ws.send_text(json.dumps(payload, default=_json_default))
                    logger.info(f"✅ Message WS envoyé à {company_id} via {ws}")
                except Exception as e:
                    logger.error(f"❌ Erreur envoi WS à {company_id}: {e}")
                    disconnected.append(ws)
            for ws in disconnected:
                self.disconnect(company_id, ws)
        else:
            logger.warning(
                f"⚠️ Aucune connexion WS active pour company_id={company_id}"
            )

# Instances globales
web_notification_manager = NotificationManager()
desktop_notification_manager = NotificationManager()
