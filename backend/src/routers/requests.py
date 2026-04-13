import json

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.orm import joinedload
from pydantic import BaseModel
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis

from src.database import get_db, get_redis
from src.models.user import User, UserRole
from src.models.request import GuestRequest, RequestType, RequestStatus
from src.schemas.requests import GuestRequestResponseSchema
from src.schemas.user import UserBase
from src.security import get_current_user
from src.services.websocket_manager import manager

router = APIRouter(prefix="/api/requests", tags=["Guest Requests"])


class CreateRequestSchema(BaseModel):
    telegram_id: int
    type: RequestType
    value: str
    comment: Optional[str] = None


@router.get("/", response_model=list[GuestRequestResponseSchema], dependencies=[Depends(get_current_user)])
async def get_requests(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(GuestRequest)
        .options(joinedload(GuestRequest.user))
        .where(GuestRequest.created_at >= func.now() - text("interval '12 hours'"))
        .where(GuestRequest.status != RequestStatus.EXPIRED)
        .order_by(GuestRequest.created_at.desc())
    )
    result = await db.execute(stmt)
    requests = result.scalars().unique().all()

    return [
        GuestRequestResponseSchema(
            id=request.id,
            type=request.type.value,
            value=request.value,
            status=request.status,
            comment=request.comment,
            created_at=request.created_at,
            user=UserBase.model_validate(request.user, from_attributes=True)
        ) for request in requests
    ]


@router.post("/{request_id}/complete")
async def complete_request(
        request_id: int,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.GUARD:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостатньо прав для закриття заявки")

    result = await db.execute(
        select(GuestRequest)
        .options(joinedload(GuestRequest.user))
        .where(GuestRequest.id == request_id)
    )
    request_obj = result.scalars().first()

    if not request_obj:
        raise HTTPException(status_code=404, detail="Заявку не знайдено")

    if request_obj.status != RequestStatus.NEW:
        raise HTTPException(status_code=400, detail="Ця заявка вже не активна")

    request_obj.status = RequestStatus.COMPLETED
    await db.commit()

    if request_obj.user and request_obj.user.telegram_id:
        req_type_str = request_obj.type.value if hasattr(request_obj.type, 'value') else request_obj.type

        event_data = {
            'event': 'request_closed',
            'resident_telegram_id': request_obj.user.telegram_id,
            'value': request_obj.value,
            'type': req_type_str,
            'processed_by': current_user.full_name or current_user.phone_number
        }

        await redis.xadd("vms_stream", {'payload': json.dumps(event_data)})

    await manager.broadcast({
        'event': 'requests_updated',
        'request_id': request_id,
        'new_status': RequestStatus.COMPLETED.value
    })

    return {"ok": True}
