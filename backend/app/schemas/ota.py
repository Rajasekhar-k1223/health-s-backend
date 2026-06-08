from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class FirmwareReleaseBase(BaseModel):
    version: str
    release_notes: Optional[str] = None
    compatibility_rules: Optional[Dict] = None
    artifact_url: str

class FirmwareReleaseCreate(FirmwareReleaseBase):
    pass

class FirmwareReleaseResponse(FirmwareReleaseBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class OTADeploymentBase(BaseModel):
    device_id: int
    target_firmware_version: str
    scheduled_time: Optional[datetime] = None

class OTADeploymentCreate(OTADeploymentBase):
    pass

class OTADeploymentResponse(OTADeploymentBase):
    id: int
    status: str

    class Config:
        from_attributes = True

class OTACheckResponse(BaseModel):
    update_available: bool
    version: Optional[str] = None
    artifact_url: Optional[str] = None
    deployment_id: Optional[int] = None
