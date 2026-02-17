from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.models.user import UserRole
from src.schemas.apartment import Apartment
from src.schemas.car import CarBase


class UserBase(BaseModel):
    phone_number: str
    role: UserRole
    full_name: Optional[str] = None
    apartment: Optional[Apartment] = None
    is_admin: Optional[bool] = False
    is_superadmin: Optional[bool] = False

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    cars: Optional[list[CarBase]] = []

    created_at: datetime
    updated_at: Optional[datetime]
