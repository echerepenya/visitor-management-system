import enum

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, BigInteger, event, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import get_history
from src.database import Base
from src.utils import normalize_phone


class UserRole(str, enum.Enum):
    RESIDENT = "resident"
    GUARD = "guard"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    phone_number = Column(String(20), unique=True, index=True, nullable=False)  # login for the bot
    role = Column(Enum(UserRole), default=UserRole.RESIDENT, nullable=False)
    full_name = Column(String(100), nullable=True)

    username = Column(String, unique=True, index=True, nullable=True)  # optional username, for admin/guard only
    hashed_password = Column(String, nullable=True)  # password for admin panel if guard/admin

    telegram_id = Column(BigInteger, unique=True, nullable=True, index=True)
    first_telegram_login_at = Column(DateTime(timezone=True), nullable=True)
    is_agreed_processing_personal_data = Column(Boolean, default=False, nullable=False)

    is_admin = Column(Boolean, default=False, nullable=False)  # access to admin panel, allowed to create/edit residents and guards
    is_superadmin = Column(Boolean, default=False, nullable=False)  # allows to create/edit all type users, buildings, apartments
    is_resident_contact = Column(Boolean, default=False, nullable=False)

    apartment_id = Column(Integer, ForeignKey("apartments.id"), nullable=True)
    apartment = relationship("Apartment", back_populates="residents", lazy="selectin", enable_typechecks=False)

    cars = relationship("Car", back_populates="owner", cascade="all, delete-orphan", passive_deletes=True, foreign_keys="Car.owner_id")
    requests = relationship("GuestRequest", back_populates="user", cascade="all, delete-orphan", passive_deletes=True, foreign_keys="GuestRequest.user_id")
    logs = relationship("UserActivityLog", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

    created_by = Column(Integer, ForeignKey("users.id", name='fk_' + __tablename__ + '_created_by_users', ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_by = Column(Integer, ForeignKey("users.id", name='fk_' + __tablename__ + '_updated_by_users', ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_by = Column(Integer, ForeignKey("users.id", name='fk_' + __tablename__ + '_deleted_by_users', ondelete="SET NULL"), nullable=True)
    deleted_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"{self.phone_number} {'('+self.full_name+')' if self.full_name else self.apartment if self.apartment else ''}"


@event.listens_for(User, 'before_insert')
def receive_before_insert(mapper, connection, target):
    target.phone_number = normalize_phone(target.phone_number)
    target.telegram_id = None


@event.listens_for(User, 'before_update')
def receive_before_update(mapper, connection, target):
    target.phone_number = normalize_phone(target.phone_number)
    
    # Check if phone_number has changed
    hist = get_history(target, 'phone_number')
    if hist.has_changes():
        target.telegram_id = None


class RestrictedUser(User):
    # just mirroring existing table
    __mapper_args__ = {
        "polymorphic_identity": "restricted",
    }


@event.listens_for(RestrictedUser, 'before_insert')
def receive_before_insert_restricted(mapper, connection, target):
    target.phone_number = normalize_phone(target.phone_number)
    target.telegram_id = None


@event.listens_for(RestrictedUser, 'before_update')
def receive_before_update_restricted(mapper, connection, target):
    target.phone_number = normalize_phone(target.phone_number)
    hist = get_history(target, 'phone_number')
    if hist.has_changes():
        target.telegram_id = None
