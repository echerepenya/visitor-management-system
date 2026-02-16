from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette import status

from src.models.apartment import Apartment
from src.models.user import User
from src.schemas.user import UserProfileSchema


async def get_user_by_telegram_id(telegram_id: int, db: AsyncSession):
    stmt = (
        select(User)
        .options(selectinload(User.apartment).selectinload(Apartment.building))
        .where(User.telegram_id == telegram_id)
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserProfileSchema(
        id=user.id,
        phone_number=user.phone_number,
        role=user.role.value,
        full_name=user.full_name,
        building=user.apartment.building.address if user.apartment else None,
        apartment_number=str(user.apartment.number) if user.apartment else None,
        is_admin=user.is_admin,
        is_superadmin=user.is_superadmin
    )
