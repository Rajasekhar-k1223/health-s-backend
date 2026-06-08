from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=True)
    action = Column(String(255), nullable=False)
    resource = Column(String(255), nullable=False)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
