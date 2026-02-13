from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from src.database import get_db
from src.models.user import User
from src.models.request import GuestRequest, RequestType, RequestStatus
from src.utils import normalize_plate

router = APIRouter(prefix="/requests", tags=["Guest Requests"])


class CreateRequestSchema(BaseModel):
    telegram_id: int
    type: RequestType
    value: str
    comment: Optional[str] = None


@router.post("/", status_code=status.HTTP_201_CREATED)
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
