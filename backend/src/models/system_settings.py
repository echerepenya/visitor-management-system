from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from src.database import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True)
    guest_parking_spots = Column(Integer, default=11, nullable=False)
    guest_parking_spots_offset = Column(Integer, default=0, nullable=False)
    guest_parking_post_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    guest_parking_post = relationship("User")
