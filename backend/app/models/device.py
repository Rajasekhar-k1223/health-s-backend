from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, index=True, nullable=False)
    serial_number = Column(String(100), unique=True, nullable=True)
    model = Column(String(50), nullable=True)
    firmware_version = Column(String(50), nullable=True)
    ownership_status = Column(String(50), nullable=True)
    device_type = Column(String(50), nullable=False)
    status = Column(String(20), default="active")
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    patient = relationship("Patient", back_populates="devices")
