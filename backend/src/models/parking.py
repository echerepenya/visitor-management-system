import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship
from src.database import Base

class ParkingStatus(str, enum.Enum):
    new = "new"
    keyfob_issued_entry = "keyfob_issued_entry"
    parked = "parked"
    keyfob_issued_exit = "keyfob_issued_exit"
    completed = "completed"
    expired = "expired"

class GuestParkingRequest(Base):
    __tablename__ = "guest_parking_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    license_plate = Column(String, index=True)
    status = Column(Enum(ParkingStatus), default=ParkingStatus.new, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="parking_requests")
    keyfob = relationship("KeyfobStatus", back_populates="current_request", uselist=False)

class KeyfobState(str, enum.Enum):
    WITH_GUARD = "WITH_GUARD"
    WITH_GUEST = "WITH_GUEST"

class KeyfobStatus(Base):
    __tablename__ = "keyfob_status"

    id = Column(Integer, primary_key=True)
    state = Column(Enum(KeyfobState), default=KeyfobState.WITH_GUARD)
    current_request_id = Column(Integer, ForeignKey("guest_parking_requests.id"), nullable=True)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    
    current_request = relationship("GuestParkingRequest", back_populates="keyfob")

class ParkingSettings(Base):
    __tablename__ = "parking_settings"

    id = Column(Integer, primary_key=True)
    spots_offset = Column(Integer, default=0)
