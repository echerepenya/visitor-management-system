import datetime
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from starlette import status
from redis.asyncio import Redis

from src.database import get_db, get_redis
from src.models.apartment import Apartment
from src.models.car import Car
from src.models.request import GuestRequest, RequestType, RequestStatus
from src.models.user import User
from src.routers.requests import CreateRequestSchema
from src.schemas.user import UserResponse
from src.security import get_api_key
from src.services.users import get_user_by_telegram_id, get_resident_contact_guard_users, log_user_activity
from src.services.websocket_manager import manager
from src.utils import normalize_plate, normalize_phone

logger = logging.getLogger(__name__)

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

    if not user.telegram_id:
        user.telegram_id = data.telegram_id
        user.first_telegram_login_at = datetime.datetime.now(datetime.UTC)
    elif user.telegram_id != data.telegram_id:
        logger.warning(f"Telegram ID reassignment attempt for user {user.id}")

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


class TelegramRequestSchema(BaseModel):
    telegram_id: Optional[int] = None


@router.post("/get-me", response_model=UserResponse)
async def get_telegram_user(payload: TelegramRequestSchema, db: AsyncSession = Depends(get_db)):
    if not payload.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram ID is required"
        )

    user = await get_user_by_telegram_id(payload.telegram_id, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await log_user_activity(db, user.id, "get_user_info")
    return user


@router.post("/car-search/{plate}")
async def check_car(
        payload: TelegramRequestSchema,
        plate: str = Path(..., min_length=1, max_length=20, pattern=r'^[A-ZА-ЯІЇЄa-zа-яіїє0-9\s\-]+$'),
        exact: bool = Query(False),
        search_mode: str = Query("full"),
        db: AsyncSession = Depends(get_db)
):
    clean_plate = normalize_plate(plate)
    if not clean_plate:
        raise HTTPException(status_code=400, detail='Неправильний формат номера')

    response_data = {
        "plate": clean_plate,
        "found": False,
        "type": None,
        "multiple": False,
        "info": {}
    }

    active_user = await get_user_by_telegram_id(payload.telegram_id, db) if payload.telegram_id else None
    if active_user:
        await log_user_activity(db, active_user.id, "car_search")

    # ==========================================
    # БЛОК 0. Пошук за частковим збігом
    # ==========================================
    if not exact and 3 <= len(clean_plate) <= 5:
        # Шукаємо у мешканців (ilike для нечутливості до регістру, % для часткового збігу)
        stmt_cars_partial = select(Car.plate_number).where(Car.plate_number.ilike(f"%{clean_plate}%")).limit(10)
        res_cars_partial = await db.execute(stmt_cars_partial)
        partial_cars = res_cars_partial.scalars().all()

        # Шукаємо у гостьових заявках
        stmt_reqs_partial = select(GuestRequest.value).where(GuestRequest.value.ilike(f"%{clean_plate}%"))

        # ДОДАНО: Якщо режим в'їзду - беремо тільки нові заявки
        if search_mode == "entry":
            stmt_reqs_partial = stmt_reqs_partial.where(GuestRequest.status == 'new')

        stmt_reqs_partial = stmt_reqs_partial.limit(10)
        res_reqs_partial = await db.execute(stmt_reqs_partial)
        partial_reqs = res_reqs_partial.scalars().all()

        # Об'єднуємо результати і прибираємо дублікати
        all_matches = list(set(partial_cars + partial_reqs))

        if len(all_matches) > 1:
            response_data["found"] = True
            response_data["multiple"] = True
            response_data["cars"] = all_matches[:10]
            return response_data
        elif len(all_matches) == 1:
            clean_plate = all_matches[0]
            response_data["plate"] = clean_plate

    # ==========================================
    # 1. Search among residents - in cars table
    # ==========================================
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
            "owner_telegram_id": car.owner.telegram_id,
            "phone": car.owner.phone_number,
            "building": apt.building.address if apt else None,
            "apartment": apt.number if apt else None
        }
        return response_data

    # ==========================================
    # 2. Else do search in guest requests - in requests table
    # ==========================================
    stmt_req = (select(GuestRequest).options(
        selectinload(GuestRequest.user).selectinload(User.apartment).selectinload(Apartment.building))
                .where(GuestRequest.value == clean_plate)
                )

    # ДОДАНО: Фільтрація по статусу для режиму в'їзду
    if search_mode == "entry":
        stmt_req = stmt_req.where(GuestRequest.status == 'new')

    stmt_req = (
        stmt_req.order_by(func.coalesce(GuestRequest.updated_at, GuestRequest.created_at).desc())
        .limit(1)
    )

    res_req = await db.execute(stmt_req)
    request = res_req.scalars().first()

    if request:
        response_data["found"] = True
        response_data["type"] = "guest"
        apt = request.user.apartment
        response_data["info"] = {
            "invited_by": request.user.full_name,
            "invited_at": (request.updated_at or request.created_at).isoformat() if (
                        request.updated_at or request.created_at) else None,
            "phone": request.user.phone_number,
            "building": apt.building.address if apt else None,
            "apartment": apt.number if apt else None,
            "request_type": getattr(request, "type", None),
            "owner_telegram_id": request.user.telegram_id,
            "status": getattr(request, "status", None)
        }
        return response_data

    # 3. Not found
    return response_data


@router.post("/create-request", status_code=status.HTTP_201_CREATED)
async def create_request(req: CreateRequestSchema, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)):
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

    guards = await get_resident_contact_guard_users(db)
    guard_telegram_ids = [guard.telegram_id for guard in guards if guard.telegram_id]

    if guard_telegram_ids:
        address = f"{user.apartment.building.address}, {user.apartment.number}" if user.apartment else "N/A"

        event_data = {
            "event": "new_guest_request",
            "guard_telegram_ids": guard_telegram_ids,
            "author_name": user.full_name,
            "author_phone": user.phone_number,
            "author_address": address,
            "value": clean_value,
            "type": new_request.type.value,
            "comment": new_request.comment
        }

        await redis.xadd("vms_stream", {"payload": json.dumps(event_data)})

    await manager.broadcast({
        'event': 'requests_updated',
        'request_id': new_request.id,
        'new_status': RequestStatus.NEW.value
    })

    return {"id": new_request.id, "status": "created"}


@router.post("/resident-contact-guards", response_model=list[UserResponse])
async def get_resident_contact_guards(payload: TelegramRequestSchema, db: AsyncSession = Depends(get_db)):
    active_user = await get_user_by_telegram_id(payload.telegram_id, db) if payload.telegram_id else None
    if active_user:
        await log_user_activity(db, active_user.id, "guard_contacts")

    return await get_resident_contact_guard_users(db)
