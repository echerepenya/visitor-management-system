from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_db
from src.schemas.parking import GuestParkingRequestOut, ParkingDashboardStatus, FreeSpotsOverride
from src.services.parking import (
    get_all_dashboard_requests,
    get_parking_status,
    issue_keyfob,
    return_keyfob,
    return_keyfob,
    reset_keyfob,
    override_free_spots
)
from src.redis import publish_event

router = APIRouter(prefix="/api/parking", tags=["parking"])

@router.get("/requests", response_model=List[GuestParkingRequestOut])
async def read_parking_requests(db: AsyncSession = Depends(get_db)):
    return await get_all_dashboard_requests(db)

@router.get("/status", response_model=ParkingDashboardStatus)
async def read_parking_status(db: AsyncSession = Depends(get_db)):
    return await get_parking_status(db)

@router.post("/{request_id}/issue-keyfob", response_model=GuestParkingRequestOut)
async def api_issue_keyfob(request_id: int, db: AsyncSession = Depends(get_db)):
    req = await issue_keyfob(db, request_id)
    await publish_event("parking_requests_updated", {"request_id": req.id, "new_status": req.status.value})
    return req

@router.post("/{request_id}/return-keyfob", response_model=GuestParkingRequestOut)
async def api_return_keyfob(request_id: int, db: AsyncSession = Depends(get_db)):
    req = await return_keyfob(db, request_id)
    await publish_event("parking_requests_updated", {"request_id": req.id, "new_status": req.status.value})
    return req

@router.post("/reset-keyfob")
async def api_reset_keyfob(db: AsyncSession = Depends(get_db)):
    res = await reset_keyfob(db)
    await publish_event("parking_requests_updated", {"action": "reset_keyfob"})
    return res

@router.post("/override-spots", response_model=ParkingDashboardStatus)
async def api_override_free_spots(payload: FreeSpotsOverride, db: AsyncSession = Depends(get_db)):
    res = await override_free_spots(db, payload.free_spots)
    await publish_event("parking_requests_updated", {"action": "override_spots"})
    return res
