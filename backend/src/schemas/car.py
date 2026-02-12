from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CarBase(BaseModel):
    plate_number: str = Field(..., max_length=20, description="Номерний знак")
    model: Optional[str] = None
    owner_phone: Optional[str] = None
    notes: Optional[str] = None


class CarCreate(CarBase):
    pass


class CarResponse(CarBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True  # Дозволяє читати дані з ORM моделі
