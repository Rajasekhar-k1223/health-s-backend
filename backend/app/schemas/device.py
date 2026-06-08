from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DeviceBase(BaseModel):
    device_id: str
    serial_number: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    ownership_status: Optional[str] = None
    device_type: str
    status: str = "active"

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    serial_number: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    ownership_status: Optional[str] = None
    status: Optional[str] = None
    patient_id: Optional[int] = None

class DeviceResponse(DeviceBase):
    id: int
    patient_id: Optional[int] = None

    class Config:
        from_attributes = True

class DeviceAssign(BaseModel):
    patient_id: Optional[int] = None

class DeviceCredentialCreate(BaseModel):
    device_id: int
    api_key_hash: str

class DeviceCredentialResponse(BaseModel):
    id: int
    device_id: int
    is_active: bool

    class Config:
        from_attributes = True
