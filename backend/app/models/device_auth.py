from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
import enum
from .base import Base

class CertStatus(str, enum.Enum):
    active = "active"
    revoked = "revoked"
    expired = "expired"

class DeviceCredential(Base):
    __tablename__ = "device_credentials"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, unique=True)
    api_key_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    device = relationship("Device")

class DeviceCertificate(Base):
    __tablename__ = "device_certificates"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    certificate_pem = Column(Text, nullable=False)
    fingerprint = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(Enum(CertStatus), default=CertStatus.active)
    valid_until = Column(DateTime(timezone=True), nullable=False)

    device = relationship("Device")
