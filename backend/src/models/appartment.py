from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base


class Apartment(Base):
    __tablename__ = "apartments"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(20), nullable=False)

    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    building = relationship("Building", back_populates="apartments")

    residents = relationship("User", back_populates="apartment")

    def __repr__(self):
        return f"Apt {self.number}"
