from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.models.request import RequestStatus, RequestType
from src.schemas.user import UserBase


class GuestRequestResponseSchema(BaseModel):
    id: int
    type: RequestType
    value: Optional[str] = None
    status: RequestStatus
    comment: Optional[str] = None
    created_at: datetime
    user: UserBase

    class Config:
        from_attributes = True
