from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from starlette import status

from src.database import get_db
from src.models.appartment import Apartment
from src.models.user import User, UserRole
from src.utils import normalize_phone

router = APIRouter(prefix="/auth", tags=["Auth"])


class UserProfileSchema(BaseModel):
    id: int
    phone_number: str
    role: UserRole
    full_name: Optional[str] = None
    building: Optional[str] = None
    apartment_number: Optional[str] = None
    is_admin: Optional[bool] = False
    is_superadmin: Optional[bool] = False


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

    if not user.is_agreed_processing_personal_data:
        user.is_agreed_processing_personal_data = True

    await db.commit()

    return {
        "status": "ok",
        "role": user.role,
        "name": user.full_name,
        "apartment": f"{user.apartment.building.address}, {user.apartment.number}" if user.apartment else "N/A",
        "is_admin": user.is_admin,
        "is_superadmin": user.is_superadmin
    }


@router.get("/telegram/{telegram_id}", response_model=UserProfileSchema, dependencies=[Depends(get_db)])
async def get_user_by_telegram(telegram_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(User)
        .options(selectinload(User.apartment).selectinload(Apartment.building))
        .where(User.telegram_id == telegram_id)
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfileSchema(
        id=user.id,
        phone_number=user.phone_number,
        role=user.role,
        full_name=user.full_name,
        building=user.apartment.building.address if user.apartment else None,
        apartment_number=str(user.apartment.number) if user.apartment else None,
        is_admin=user.is_admin,
        is_superadmin=user.is_superadmin
    )
