from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from src.models.parking import GuestParkingRequest, ParkingStatus, KeyfobStatus, KeyfobState, ParkingSettings
from src.models.user import User
from src.models.apartment import Apartment
from src.schemas.parking import GuestParkingRequestCreate, ParkingDashboardStatus, KeyfobStatusOut, KeyfobGuestInfo

PARKING_SPOTS = 11

async def get_active_parking_requests(db: AsyncSession):
    stmt = select(GuestParkingRequest).where(
        GuestParkingRequest.status.in_([
            ParkingStatus.new,
            ParkingStatus.keyfob_issued_entry,
            ParkingStatus.parked,
            ParkingStatus.keyfob_issued_exit
        ])
    ).order_by(GuestParkingRequest.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_all_dashboard_requests(db: AsyncSession):
    # Today's requests + all active
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    stmt = select(GuestParkingRequest).options(
        selectinload(GuestParkingRequest.user).selectinload(User.cars)
    ).where(
        (GuestParkingRequest.status.in_([
            ParkingStatus.new,
            ParkingStatus.keyfob_issued_entry,
            ParkingStatus.parked,
            ParkingStatus.keyfob_issued_exit
        ])) | (GuestParkingRequest.created_at >= today_start)
    ).order_by(GuestParkingRequest.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_parking_settings(db: AsyncSession) -> ParkingSettings:
    stmt = select(ParkingSettings).where(ParkingSettings.id == 1)
    result = await db.execute(stmt)
    settings = result.scalars().first()
    if not settings:
        settings = ParkingSettings(id=1, spots_offset=0)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings

async def get_parking_status(db: AsyncSession) -> ParkingDashboardStatus:
    active_requests = await get_active_parking_requests(db)
    occupied = len(active_requests)
    
    settings = await get_parking_settings(db)
    calculated_free = PARKING_SPOTS - occupied
    free = max(0, min(PARKING_SPOTS, calculated_free + settings.spots_offset))

    
    # Get Keyfob status
    stmt = select(KeyfobStatus).where(KeyfobStatus.id == 1)
    result = await db.execute(stmt)
    keyfob = result.scalars().first()
    
    if not keyfob:
        keyfob = KeyfobStatus(id=1, state=KeyfobState.WITH_GUARD)
        db.add(keyfob)
        await db.commit()
        await db.refresh(keyfob)

    overdue = False
    guest_info = None
    
    if keyfob.state == KeyfobState.WITH_GUEST and keyfob.current_request_id:
        if keyfob.issued_at:
            time_diff = datetime.now(timezone.utc) - keyfob.issued_at
            if time_diff > timedelta(minutes=30):
                overdue = True
        
        # Load guest info
        req_stmt = select(GuestParkingRequest).where(GuestParkingRequest.id == keyfob.current_request_id)
        req_res = await db.execute(req_stmt)
        req = req_res.scalars().first()
        
        if req:
            apt_num = None
            user_stmt = select(User).where(User.id == req.user_id)
            user_res = await db.execute(user_stmt)
            user = user_res.scalars().first()
            if user and user.apartment_id:
                apt_stmt = select(Apartment).where(Apartment.id == user.apartment_id)
                apt_res = await db.execute(apt_stmt)
                apt = apt_res.scalars().first()
                if apt:
                    apt_num = apt.number

            guest_info = KeyfobGuestInfo(
                license_plate=req.license_plate,
                apartment_number=str(apt_num) if apt_num else None
            )

    keyfob_out = KeyfobStatusOut(
        state=keyfob.state,
        request_id=keyfob.current_request_id,
        issued_at=keyfob.issued_at,
        overdue=overdue,
        guest_info=guest_info
    )

    return ParkingDashboardStatus(
        total_spots=PARKING_SPOTS,
        occupied_spots=occupied,
        free_spots=free,
        keyfob=keyfob_out
    )

async def create_parking_request(db: AsyncSession, request_data: GuestParkingRequestCreate, user_id: int):
    # Check capacity
    status = await get_parking_status(db)
    if status.free_spots <= 0:
        raise HTTPException(status_code=400, detail="Немає вільних паркомісць")
    
    db_request = GuestParkingRequest(
        user_id=user_id,
        license_plate=request_data.license_plate,
        status=ParkingStatus.new
    )
    db.add(db_request)
    await db.commit()
    await db.refresh(db_request)
    return db_request

async def get_keyfob(db: AsyncSession) -> KeyfobStatus:
    stmt = select(KeyfobStatus).where(KeyfobStatus.id == 1)
    result = await db.execute(stmt)
    keyfob = result.scalars().first()
    if not keyfob:
        keyfob = KeyfobStatus(id=1, state=KeyfobState.WITH_GUARD)
        db.add(keyfob)
        await db.commit()
        await db.refresh(keyfob)
    return keyfob

async def issue_keyfob(db: AsyncSession, request_id: int):
    req_stmt = select(GuestParkingRequest).where(GuestParkingRequest.id == request_id)
    req_res = await db.execute(req_stmt)
    req = req_res.scalars().first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Заявку не знайдено")
        
    keyfob = await get_keyfob(db)
    if keyfob.state != KeyfobState.WITH_GUARD:
        raise HTTPException(status_code=400, detail="Брелок зараз у іншого гостя")
        
    if req.status == ParkingStatus.new:
        req.status = ParkingStatus.keyfob_issued_entry
    elif req.status == ParkingStatus.parked:
        req.status = ParkingStatus.keyfob_issued_exit
    else:
        raise HTTPException(status_code=400, detail="Некоректний статус для видачі брелока")
        
    keyfob.state = KeyfobState.WITH_GUEST
    keyfob.current_request_id = req.id
    keyfob.issued_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    refresh_stmt = select(GuestParkingRequest).options(
        selectinload(GuestParkingRequest.user).selectinload(User.cars)
    ).where(GuestParkingRequest.id == request_id)
    refresh_res = await db.execute(refresh_stmt)
    return refresh_res.scalars().first()

async def return_keyfob(db: AsyncSession, request_id: int):
    req_stmt = select(GuestParkingRequest).where(GuestParkingRequest.id == request_id)
    req_res = await db.execute(req_stmt)
    req = req_res.scalars().first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Заявку не знайдено")
        
    keyfob = await get_keyfob(db)
    if keyfob.state != KeyfobState.WITH_GUEST or keyfob.current_request_id != req.id:
        raise HTTPException(status_code=400, detail="Брелок не знаходиться у цього гостя")
        
    if req.status == ParkingStatus.keyfob_issued_entry:
        req.status = ParkingStatus.parked
    elif req.status == ParkingStatus.keyfob_issued_exit:
        req.status = ParkingStatus.completed
    else:
        raise HTTPException(status_code=400, detail="Некоректний статус для повернення брелока")
        
    keyfob.state = KeyfobState.WITH_GUARD
    keyfob.current_request_id = None
    keyfob.issued_at = None
    
    await db.commit()

    refresh_stmt = select(GuestParkingRequest).options(
        selectinload(GuestParkingRequest.user).selectinload(User.cars)
    ).where(GuestParkingRequest.id == request_id)
    refresh_res = await db.execute(refresh_stmt)
    return refresh_res.scalars().first()

async def reset_keyfob(db: AsyncSession):
    keyfob = await get_keyfob(db)
    keyfob.state = KeyfobState.WITH_GUARD
    keyfob.current_request_id = None
    keyfob.issued_at = None
    await db.commit()
    return {"message": "Брелок успішно скинуто"}

async def check_expired_parking_requests(db: AsyncSession):
    now = datetime.now(timezone.utc)
    timeout_threshold = now - timedelta(minutes=30)
    
    stmt = select(GuestParkingRequest).where(
        GuestParkingRequest.status == ParkingStatus.new,
        GuestParkingRequest.created_at <= timeout_threshold
    )
    result = await db.execute(stmt)
    expired_requests = result.scalars().all()
    
    for req in expired_requests:
        req.status = ParkingStatus.expired
        
    if expired_requests:
        await db.commit()
    return expired_requests

async def override_free_spots(db: AsyncSession, new_free_spots: int):
    active_requests = await get_active_parking_requests(db)
    occupied = len(active_requests)
    calculated_free = PARKING_SPOTS - occupied
    
    offset = new_free_spots - calculated_free
    
    settings = await get_parking_settings(db)
    settings.spots_offset = offset
    await db.commit()
    
    return await get_parking_status(db)

