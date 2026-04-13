from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.database import Base


class Apartment(Base):
    __tablename__ = "apartments"
    __table_args__ = (
        Index('idx_apartments_number_building_id', 'number', 'building_id', unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(20), nullable=False)

    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    building = relationship("Building", back_populates="apartments", lazy="selectin")

    residents = relationship("User", back_populates="apartment")

    def __str__(self):
        if "building" in self.__dict__ and self.building:
            return f"{self.building.address}, {self.number}"
        return f"Кв. {self.number}"

    def __repr__(self):
        return f"<Apartment id={self.id} number={self.number}>"
