from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class MedicalHistoryBase(BaseModel):
    condition: str
    diagnosed_date: Optional[date] = None
    status: str = "active"
    notes: Optional[str] = None

class MedicalHistoryCreate(MedicalHistoryBase):
    pass

class MedicalHistoryResponse(MedicalHistoryBase):
    id: int
    patient_id: int

    class Config:
        from_attributes = True

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    age: int
    mrn: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    contact_number: Optional[str] = None
    address: Optional[str] = None
    priority: str = "low"
    primary_doctor_id: Optional[int] = None
    user_id: Optional[int] = None
    ward_id: Optional[int] = None

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    id: int
    risk_score: float
    medical_history: List[MedicalHistoryResponse] = []

    class Config:
        from_attributes = True
