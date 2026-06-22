from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum

class RoleEnum(str, enum.Enum):
    super_admin = "super_admin"
    hospital_admin = "hospital_admin"
    doctor = "doctor"
    nurse = "nurse"
    patient = "patient"
    device = "device"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    contact_number = Column(String(20), nullable=True)
    
    role = Column(Enum(RoleEnum), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    organization_id = Column(String(36), ForeignKey("organization.id"), nullable=True)
    organization = relationship("AdminOrganization")
    encounters = relationship("Encounter", back_populates="doctor")
