import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from starlette import status

from src.models.apartment import Apartment
from src.models.car import Car
from src.models.user import User, UserRole
from src.models.user_activity_log import UserActivityLog
from src.schemas.car import CarResponse
from src.schemas.user import UserResponse, UserBase


async def get_user_by_telegram_id(telegram_id: int, db: AsyncSession) -> UserResponse | None:
    stmt = (
        select(User)
        .options(selectinload(User.apartment).selectinload(Apartment.building))
        .where(User.telegram_id == telegram_id)
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        return None

    cars_result = await db.execute(
        select(Car)
        .where(Car.owner_id == user.id)
    )
    cars = cars_result.scalars().all()

    cohabitants = []
    if user.apartment_id:
        cohabitants_result = await db.execute(
            select(User)
            .options(selectinload(User.apartment))
            .where(
                User.apartment_id == user.apartment_id,
                User.id != user.id
            )
        )
        cohabitants = cohabitants_result.scalars().all()

    return UserResponse(
        id=user.id,
        phone_number=user.phone_number,
        role=user.role.value,
        full_name=user.full_name,
        building=user.apartment.building.address if user.apartment else None,
        apartment_number=str(user.apartment.number) if user.apartment else None,
        is_admin=user.is_admin,
        is_superadmin=user.is_superadmin,
        cars=[
            CarResponse(
                id=car.id,
                plate_number=car.plate_number,
                model=car.model,
                notes=car.notes
            ) for car in cars
        ],
        cohabitants=[
            UserBase(
                phone_number=cohabitant.phone_number,
                role=cohabitant.role.value,
                full_name=cohabitant.full_name,
                apartment=cohabitant.apartment
            ) for cohabitant in cohabitants
        ],
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


async def get_resident_contact_guard_users(db: AsyncSession):
    guards_stmt = select(User).where(
        User.role == UserRole.GUARD,
        User.is_resident_contact.is_(True)
    )
    result = await db.execute(guards_stmt)
    guards = result.scalars().all()

    return [
        UserResponse(
            id=user.id,
            telegram_id=user.telegram_id,
            phone_number=user.phone_number,
            role=user.role.value,
            is_resident_contact=user.is_resident_contact,
            full_name=user.full_name,
        ) for user in guards
    ]


async def log_user_activity(db: AsyncSession, user_id: int, action: str, details: dict = None):
    try:
        new_log_record = UserActivityLog(user_id=user_id, action=action, details=details)
        db.add(new_log_record)
        await db.commit()

    except SQLAlchemyError as e:
        await db.rollback()
        logging.error(f"Failed to log activity for {user_id}: {e}")

    except Exception as e:
        await db.rollback()
        logging.error(f"Unexpected error in log_activity: {e}")
