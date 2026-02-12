from sqlalchemy import Column, Integer, String, DateTime, Text, func
from src.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_username = Column(String, index=True)
    action = Column(String)         # CREATE, UPDATE, DELETE
    target_model = Column(String)   # Car, User, House
    details = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
