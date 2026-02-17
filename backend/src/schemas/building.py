from pydantic import BaseModel


class Building(BaseModel):
    id: int
    address: str

    class Config:
        from_attributes = True
