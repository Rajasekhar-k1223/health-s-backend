from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TelehealthSessionBase(BaseModel):
    patient_id: int
    doctor_id: int
    scheduled_time: datetime
    duration_minutes: int = 30
    notes: Optional[str] = None
    meeting_url: Optional[str] = None

class TelehealthSessionCreate(TelehealthSessionBase):
    pass

class TelehealthSessionUpdate(BaseModel):
    status: Optional[str] = None
    meeting_url: Optional[str] = None

class TelehealthSessionResponse(TelehealthSessionBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
