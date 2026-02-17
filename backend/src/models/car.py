from sqlalchemy import Integer, String, Boolean, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship, mapped_column
from src.database import Base
from src.utils import normalize_plate
from sqlalchemy import event


class Car(Base):
    __tablename__ = "cars"

    id = mapped_column(Integer, primary_key=True, index=True)

    plate_number = mapped_column(String(20), unique=True, index=True, nullable=False)
    model = mapped_column(String(100), nullable=True)
    notes = mapped_column(Text, nullable=True)

    owner_id = mapped_column(Integer, ForeignKey("users.id", name='fk_' + __tablename__ + '_owner_id_users', ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="cars", lazy="selectin")

    created_at = mapped_column(DateTime, server_default=func.now())
    updated_at = mapped_column(DateTime, onupdate=func.now())

    def __repr__(self):
        return f"{self.plate_number}"


@event.listens_for(Car, 'before_insert')
@event.listens_for(Car, 'before_update')
def receive_before_insert(mapper, connection, target):
    target.plate_number = normalize_plate(target.plate_number)
