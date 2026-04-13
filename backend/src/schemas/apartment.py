from pydantic import BaseModel

from src.schemas.building import Building


class Apartment(BaseModel):
    id: int
    number: str
    building: Building

    class Config:
        from_attributes = True
