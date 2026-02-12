from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.database import Base


class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, index=True, nullable=False)

    apartments = relationship("Apartment", back_populates="building", cascade="all, delete-orphan")

    def __repr__(self):
        return self.address
