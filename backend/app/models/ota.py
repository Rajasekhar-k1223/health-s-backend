from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
import enum
from .base import Base

class OTAStatus(str, enum.Enum):
    pending = "pending"
    downloading = "downloading"
    installing = "installing"
    success = "success"
    failed = "failed"
    rolled_back = "rolled_back"

class FirmwareRelease(Base):
    __tablename__ = "firmware_releases"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, nullable=False, index=True)
    release_notes = Column(Text, nullable=True)
    compatibility_rules = Column(JSON, nullable=True)
    artifact_url = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

class OTADeployment(Base):
    __tablename__ = "ota_deployments"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    target_firmware_version = Column(String(50), ForeignKey("firmware_releases.version"), nullable=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(OTAStatus), default=OTAStatus.pending)

    device = relationship("Device")
    firmware = relationship("FirmwareRelease")
