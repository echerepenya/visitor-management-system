import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, BigInteger, event, DateTime, func
from sqlalchemy.orm import relationship
from src.database import Base
from src.utils import normalize_phone


class UserRole(str, enum.Enum):
    RESIDENT = "resident"  # bot only
    GUARD = "guard"  # bot + requests dashboard


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    phone_number = Column(String(20), unique=True, index=True, nullable=False)  # login for the bot
    username = Column(String, unique=True, index=True, nullable=True)  # optional username, for admin/guard only
    hashed_password = Column(String, nullable=True)  # password for admin panel if guard/admin
    telegram_id = Column(BigInteger, unique=True, nullable=True, index=True)

    role = Column(Enum(UserRole), default=UserRole.RESIDENT, nullable=False)
    full_name = Column(String(100), nullable=True)

    is_agreed_processing_personal_data = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)  # access to admin panel, allowed to create/edit residents and guards
    is_superadmin = Column(Boolean, default=False, nullable=False)  # allows to create/edit all type users, buildings, apartments

    apartment_id = Column(Integer, ForeignKey("apartments.id"), nullable=True)
    apartment = relationship("Apartment", back_populates="residents", lazy="selectin")

    cars = relationship("Car", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True)
    requests = relationship("GuestRequest", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now())

    def __repr__(self):
        return f"{self.phone_number} {'('+self.full_name+')' if self.full_name else self.apartment if self.apartment else ''}"


@event.listens_for(User, 'before_insert')
@event.listens_for(User, 'before_update')
def receive_before_insert(mapper, connection, target):
    target.phone_number = normalize_phone(target.phone_number)


class RestrictedUser(User):
    # just mirroring existing table
    __mapper_args__ = {
        "polymorphic_identity": "restricted",
    }


@event.listens_for(RestrictedUser, 'before_insert')
@event.listens_for(RestrictedUser, 'before_update')
def receive_before_insert(mapper, connection, target):
    target.phone_number = normalize_phone(target.phone_number)
