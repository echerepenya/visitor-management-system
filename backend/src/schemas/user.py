from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.models.user import UserRole
from src.schemas.apartment import Apartment
from src.schemas.car import CarBase


class UserBase(BaseModel):
    telegram_id: Optional[int] = None
    phone_number: str
    role: UserRole
    full_name: Optional[str] = None
    apartment: Optional[Apartment] = None
    is_admin: Optional[bool] = False
    is_superadmin: Optional[bool] = False
    is_resident_contact: Optional[bool] = False
    is_deleted: bool = False

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    building: Optional[str] = None
    apartment_number: Optional[str] = None

    cars: Optional[list[CarBase]] = []
    cohabitants: Optional[list[UserBase]] = []

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
