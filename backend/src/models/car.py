from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base
from src.utils import normalize_plate
from sqlalchemy import event


class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)

    plate_number = Column(String(20), unique=True, index=True, nullable=False)
    model = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="cars")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def __repr__(self):
        return f"{self.plate_number}"


@event.listens_for(Car, 'before_insert')
@event.listens_for(Car, 'before_update')
def receive_before_insert(mapper, connection, target):
    target.plate_number = normalize_plate(target.plate_number)
