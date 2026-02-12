from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.models.appartment import Apartment
from src.models.car import Car
from src.models.request import GuestRequest
from src.models.user import User
from src.schemas.car import CarResponse
from src.utils import normalize_plate

router = APIRouter(prefix="/api/cars", tags=["Cars"])


@router.get("/check/{plate}")
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
            "address": address
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
            "comment": request.comment
        }
        return response_data

    # 3. Not found
    return response_data
