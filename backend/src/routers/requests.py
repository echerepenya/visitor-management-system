import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from src.database import get_db
from src.models.user import User
from src.models.request import GuestRequest, RequestType, RequestStatus
from src.security import get_api_key
from src.utils import normalize_plate

router = APIRouter(prefix="/requests", tags=["Guest Requests"])


class CreateRequestSchema(BaseModel):
    telegram_id: int
    type: RequestType
    value: str
    comment: Optional[str] = None


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_api_key)])
async def create_request(req: CreateRequestSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.telegram_id == req.telegram_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found. Please register via /start")

    clean_value = req.value
    if req.type in [RequestType.GUEST_CAR, RequestType.TAXI]:
        clean_value = normalize_plate(req.value)

    new_request = GuestRequest(
        user_id=user.id,
        type=req.type,
        value=clean_value,
        comment=req.comment,
        status=RequestStatus.NEW
    )

    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)

    return {"id": new_request.id, "status": "created"}


async def check_admin_session(request: Request):
    token = request.session.get("token")
    role = request.session.get("role")

    if not token or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )
    return token


@router.post("/{request_id}/complete", dependencies=[Depends(check_admin_session)])
async def complete_request_ui(request_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    # 1. Шукаємо заявку
    result = await db.execute(select(GuestRequest).where(GuestRequest.id == request_id))
    request_obj = result.scalars().first()

    if not request_obj:
        raise HTTPException(status_code=404, detail="Заявку не знайдено")

    if request_obj.status != RequestStatus.NEW:
        raise HTTPException(status_code=400, detail="Ця заявка вже не активна")

    # 2. Оновлюємо статус
    request_obj.status = RequestStatus.COMPLETED

    # 3. Логіка Telegram (копія з твого on_model_change, бо ModelView події тут не спрацюють)
    try:
        user_result = await db.execute(select(User).where(User.id == request_obj.user_id))
        user = user_result.scalars().first()

        if user and user.telegram_id:
            bot_token = os.getenv("BOT_TOKEN")
            msg_text = (
                f"✅ **Ваш гість заїхав!**\n\n"
                f"🚗 Авто: {request_obj.value}\n"
                f"🕒 {request_obj.visit_date.strftime('%H:%M')}"
            )

            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
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
