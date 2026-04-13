import datetime
import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import AsyncSessionLocal, get_redis
from src.models.request import GuestRequest, RequestStatus
from src.services.websocket_manager import manager

PASS_REQUEST_EXPIRATION_HOURS: int = 8


async def check_expired_requests():
    redis = await get_redis()

    async with AsyncSessionLocal() as session:
        expiration_hours_ago = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=PASS_REQUEST_EXPIRATION_HOURS)

        stmt = (
            select(GuestRequest)
            .options(selectinload(GuestRequest.user))
            .where(
                GuestRequest.status == RequestStatus.NEW.value,
                GuestRequest.created_at <= expiration_hours_ago
            )
        )

        result = await session.execute(stmt)
        expired_requests = result.scalars().all()

        for req in expired_requests:
            req.status = RequestStatus.EXPIRED.value

            if req.user and req.user.telegram_id:
                event_data = {
                    "event": "request_expired",
                    "expiration_hours": PASS_REQUEST_EXPIRATION_HOURS,
                    "resident_telegram_id": req.user.telegram_id,
                    "value": req.value,
                    "type": req.type.value if hasattr(req.type, 'value') else req.type
                }
                await redis.xadd("vms_stream", {"payload": json.dumps(event_data)})

        await session.commit()

        if expired_requests:
            await manager.broadcast({
                'event': 'requests_updated',
                'new_status': RequestStatus.EXPIRED.value
            })

            logging.info(f"⏰ Оновлено {len(expired_requests)} заявок у статус expired")
