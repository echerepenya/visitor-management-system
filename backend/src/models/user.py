import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, BigInteger, event
from sqlalchemy.orm import relationship
from src.database import Base
from src.utils import normalize_phone


class UserRole(str, enum.Enum):
    RESIDENT = "resident"  # bot only
    GUARD = "guard"  # bot + limited access to admin panel
    ADMIN = "admin"  # full admin panel access
    SUPERUSER = "superuser"  # admin + can create/delete admins


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    phone_number = Column(String(20), unique=True, index=True, nullable=False)  # login for the bot
    username = Column(String, unique=True, index=True, nullable=True)  # optional username, for admin/guard only
    hashed_password = Column(String, nullable=True)  # password for admin panel if guard/admin
    telegram_id = Column(BigInteger, unique=True, nullable=True, index=True)

    role = Column(Enum(UserRole), default=UserRole.RESIDENT, nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)

    apartment_id = Column(Integer, ForeignKey("apartments.id"), nullable=True)
    apartment = relationship("Apartment", back_populates="residents")

    cars = relationship("Car", back_populates="owner", cascade="all, delete-orphan")
    requests = relationship("GuestRequest", back_populates="user")

    def __repr__(self):
        return f"{self.full_name or self.phone_number} ({self.role})"


@event.listens_for(User, 'before_insert')
@event.listens_for(User, 'before_update')
def receive_before_insert(mapper, connection, target):
    target.phone_number = normalize_phone(target.phone_number)
