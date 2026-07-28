from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from src.models.parking import ParkingStatus, KeyfobState
from src.schemas.user import UserResponse

class GuestParkingRequestCreate(BaseModel):
    license_plate: str

class FreeSpotsOverride(BaseModel):
    free_spots: int

class KeyfobGuestInfo(BaseModel):
    license_plate: str
    apartment_number: Optional[str] = None

class KeyfobStatusOut(BaseModel):
    state: KeyfobState
    request_id: Optional[int]
    issued_at: Optional[datetime]
    overdue: bool
    guest_info: Optional[KeyfobGuestInfo]
    model_config = ConfigDict(from_attributes=True)

class GuestParkingRequestOut(BaseModel):
    id: int
    user_id: int
    license_plate: str
    status: ParkingStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)

class ParkingDashboardStatus(BaseModel):
    total_spots: int
    occupied_spots: int
    free_spots: int
    keyfob: KeyfobStatusOut
