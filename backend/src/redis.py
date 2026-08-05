import json
import logging
from src.database import get_redis
from src.services.websocket_manager import manager

logger = logging.getLogger(__name__)

async def publish_event(event_type: str, data: dict = None):
    # Broadcast to WebSocket
    ws_message = {"event": event_type}
    if data:
        ws_message.update(data)
    await manager.broadcast(ws_message)
    
    # Publish to Redis stream for Telegram bot
    try:
        redis = await get_redis()
        event_data = {"event": event_type}
        if data:
            event_data.update(data)
        await redis.xadd("vms_stream", {"payload": json.dumps(event_data)})
    except Exception as e:
        logger.error(f"Error publishing event to Redis: {e}")
