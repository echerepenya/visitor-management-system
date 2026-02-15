from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette import status

from src.database import get_db
from src.models.appartment import Apartment
from src.models.car import Car
from src.models.request import GuestRequest, RequestType, RequestStatus
from src.models.user import User, UserRole
from src.routers.requests import CreateRequestSchema
from src.security import get_api_key
from src.utils import normalize_plate, normalize_phone

router = APIRouter(prefix="/api/telegram", tags=["Telegram"], dependencies=[Depends(get_api_key)])


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


@router.post("/login")
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


@router.get("/user/{telegram_id}", response_model=UserProfileSchema, dependencies=[Depends(get_db)])
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


@router.get("/find-car/{plate}")
async def check_car(plate: str, db: AsyncSession = Depends(get_db)):
    clean_plate = normalize_plate(plate)

    response_data = {
        "plate": clean_plate,
        "found": False,
        "type": None,
        "info": None
    }

    # 1. Search among residents - in cars table
    stmt_car = (
        select(Car).options(selectinload(Car.owner).selectinload(User.apartment).selectinload(Apartment.building))
        .where(Car.plate_number == clean_plate)
    )
    res_car = await db.execute(stmt_car)
    car = res_car.scalars().first()

    if car:
        response_data["found"] = True
        response_data["type"] = "resident"

        apt = car.owner.apartment
        address = f"{apt.building.address}, кв. {apt.number}" if apt else "Не прив'язаний"
        response_data["info"] = {
            "owner": car.owner.full_name,
            "phone": car.owner.phone_number,
            "address": address,
            "user_role": request.user.role.value if request.user else UserRole.RESIDENT
        }
        return response_data

    # 2. Else do search in guest requests - in requests table
    stmt_req = (select(GuestRequest).options(
        selectinload(GuestRequest.user).selectinload(User.apartment).selectinload(Apartment.building))
        .where(GuestRequest.value == clean_plate)
    )
    res_req = await db.execute(stmt_req)
    request = res_req.scalars().first()

    if request:
        response_data["found"] = True
        response_data["type"] = "guest"
        apt = request.user.apartment
        address = f"{apt.building.address}, кв. {apt.number}" if apt else "Не прив'язаний"
        response_data["info"] = {
            "invited_by": request.user.full_name,
            "address": address,
            "comment": request.comment,
            "user_role": request.user.role.value if request.user else UserRole.RESIDENT
        }
        return response_data

    # 3. Not found
    return response_data


@router.post("/create-request", status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_api_key)])
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
