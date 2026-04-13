from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, DateTime, func, JSON
from sqlalchemy.orm import relationship
from src.database import Base


class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id = Column(BigInteger, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="logs", lazy="selectin")

    action = Column(String, nullable=False)
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
