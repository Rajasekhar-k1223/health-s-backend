from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class AlertType(str, Enum):
    CARDIAC = "Cardiac"
    RESPIRATORY = "Respiratory"
    FEVER = "Fever"
    FALL = "Fall"
    DEVICE_FAILURE = "Device Failure"

class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertBase(BaseModel):
    patient_id: int
    device_id: str
    alert_type: AlertType
    severity: SeverityLevel
    metric: str
    value: float
    message: str

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: int
    severity_score: Optional[int] = None
    ai_insight: Optional[str] = None
    is_acknowledged: bool
    acknowledged_by: Optional[int] = None
    is_resolved: bool
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class AlertResolve(BaseModel):
    resolution_notes: str
