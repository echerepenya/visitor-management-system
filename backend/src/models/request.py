import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, func
from sqlalchemy.orm import relationship
from src.database import Base


class RequestStatus(str, enum.Enum):
    NEW = "new"
    COMPLETED = "completed"
    EXPIRED = "expired"


class RequestType(str, enum.Enum):
    GUEST_CAR = "guest_car"
    TAXI = "taxi"
    DELIVERY = "delivery"
    GUEST_FOOT = "guest_foot"


class GuestRequest(Base):
    __tablename__ = "guest_requests"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", name='fk_' + __tablename__ + '_user_id_users', ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="requests")

    type = Column(Enum(RequestType), default=RequestType.GUEST_CAR, nullable=False)
    value = Column(String(100), nullable=True)  # "AA0000AA" or "Glovo delivery"
    comment = Column(Text, nullable=True)

    status = Column(Enum(RequestStatus), default=RequestStatus.NEW, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def __repr__(self):
        return f"Request #{self.id} ({self.status})"
