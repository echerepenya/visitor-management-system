from typing import Optional

from pydantic import BaseModel

from src.models.user import UserRole


class UserProfileSchema(BaseModel):
    id: int
    phone_number: str
    role: UserRole
    full_name: Optional[str] = None
    building: Optional[str] = None
    apartment_number: Optional[str] = None
    is_admin: Optional[bool] = False
    is_superadmin: Optional[bool] = False
