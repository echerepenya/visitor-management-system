from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette import status

from src.database import get_db
from src.models.apartment import Apartment
from src.models.car import Car
from src.models.request import GuestRequest, RequestType, RequestStatus
from src.models.user import User
from src.routers.requests import CreateRequestSchema
from src.schemas.user import UserResponse
from src.security import get_api_key
from src.services.users import get_user_by_telegram_id
from src.utils import normalize_plate, normalize_phone

router = APIRouter(prefix="/api/telegram", tags=["Telegram"], dependencies=[Depends(get_api_key)])


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


@router.get("/user/{telegram_id}", response_model=UserResponse, dependencies=[Depends(get_db)])
async def get_telegram_user(telegram_id: int, db: AsyncSession = Depends(get_db)):
    return await get_user_by_telegram_id(telegram_id, db)


@router.get("/car-search/{plate}")
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
        response_data["info"] = {
            "owner": car.owner.full_name,
            "phone": car.owner.phone_number,
            "building": apt.building.address if apt else None,
            "apartment": apt.number if apt else None
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
        response_data["info"] = {
            "invited_by": request.user.full_name,
            "phone": request.user.phone_number,
            "building": apt.building.address if apt else None,
            "apartment": apt.number if apt else None,
            "request_type": request.type,
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
