import os


import httpx
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from pydantic import BaseModel
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm

from src.database import get_db
from src.models.user import User, UserRole
from src.models.request import GuestRequest, RequestType, RequestStatus
from src.security import get_current_user

BOT_TOKEN = os.getenv("BOT_TOKEN")

router = APIRouter(prefix="/api/requests", tags=["Guest Requests"])


async def check_guard_session(request: Request):
    token = request.session.get("token")
    role = request.session.get("role")

    if not token or not role or role != UserRole.GUARD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )
    return token


class CreateRequestSchema(BaseModel):
    telegram_id: int
    type: RequestType
    value: str
    comment: Optional[str] = None


class GuestRequestResponseSchema(BaseModel):
    id: int
    type: str
    value: str
    status: str
    comment: Optional[str] = None
    created_at: datetime


@router.get("/", response_model=list[GuestRequestResponseSchema], dependencies=[Depends(get_current_user)])
async def get_requests(db: AsyncSession = Depends(get_db)):
    stmt = select(GuestRequest).where(GuestRequest.created_at >= func.now() - text("interval '12 hours'")).order_by(GuestRequest.created_at.desc())
    result = await db.execute(stmt)
    requests = result.scalars().all()

    return [
        GuestRequestResponseSchema(
            id=request.id,
            type=request.type.value,
            value=request.value,
            status=request.status,
            comment=request.comment,
            created_at=request.created_at
        ) for request in requests
    ]


@router.post("/{request_id}/complete", dependencies=[Depends(get_current_user)])
async def complete_request(request_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GuestRequest).where(GuestRequest.id == request_id))
    request_obj = result.scalars().first()

    if not request_obj:
        raise HTTPException(status_code=404, detail="Заявку не знайдено")

    if request_obj.status != RequestStatus.NEW:
        raise HTTPException(status_code=400, detail="Ця заявка вже не активна")

    request_obj.status = RequestStatus.COMPLETED

    try:
        user_result = await db.execute(select(User).where(User.id == request_obj.user_id))
        user = user_result.scalars().first()

        if user and user.telegram_id:
            msg_text = (
                f"✅ **Ваш гість заїхав!**\n\n"
                f"🚗 Авто: {request_obj.value}\n"
                f"🕒 {request_obj.visit_date.strftime('%H:%M')}"
            )

            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": user.telegram_id,
                        "text": msg_text,
                        "parse_mode": "Markdown"
                    }
                )
    except Exception as e:
        print(f"Telegram Error: {e}")

    await db.commit()
    return {"ok": True}
