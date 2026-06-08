from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class InsightBase(BaseModel):
    patient_id: int
    risk_category: str
    score: float
    summary: str

class InsightCreate(InsightBase):
    pass

class InsightResponse(InsightBase):
    id: int
    is_reviewed: bool
    timestamp: datetime

    class Config:
        from_attributes = True

class NoteBase(BaseModel):
    patient_id: int
    content: str
    action_item: Optional[str] = None

class NoteCreate(NoteBase):
    pass

class NoteResponse(NoteBase):
    id: int
    doctor_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class PatientRiskSummary(BaseModel):
    patient_id: int
    overall_risk_score: float
    priority: str
    recent_insights: List[InsightResponse]
    recent_notes: List[NoteResponse]
