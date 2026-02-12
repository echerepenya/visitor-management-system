from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from starlette import status

from src.database import get_db
from src.models.appartment import Apartment
from src.models.user import User
from src.utils import normalize_phone

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class TelegramLoginSchema(BaseModel):
    phone: str
    telegram_id: int
    first_name: str | None = None


@router.post("/telegram")
async def telegram_login(data: TelegramLoginSchema, db: AsyncSession = Depends(get_db)):
    clean_phone = normalize_phone(data.phone)

    stmt = (
        select(User)
        .options(
            selectinload(User.apartment)
            .selectinload(Apartment.building)
        )
        .where(User.phone_number == clean_phone)
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phone not found")

    user.telegram_id = data.telegram_id
    if data.first_name and user.full_name is None:
        user.full_name = data.first_name

    await db.commit()

    return {
        "status": "ok",
        "role": user.role,
        "name": user.full_name,
        "apartment": f"{user.apartment.building.address}, {user.apartment.number}" if user.apartment else "N/A"
    }
