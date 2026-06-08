from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CareProgramBase(BaseModel):
    name: str
    description: Optional[str] = None
    duration_days: int = 90

class CareProgramCreate(CareProgramBase):
    pass

class CareProgramResponse(CareProgramBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class EnrollmentBase(BaseModel):
    patient_id: int
    program_id: int

class EnrollmentCreate(EnrollmentBase):
    pass

class EnrollmentUpdate(BaseModel):
    status: Optional[str] = None
    adherence_score: Optional[float] = None

class EnrollmentResponse(EnrollmentBase):
    id: int
    enrollment_date: datetime
    status: str
    adherence_score: float
    program: Optional[CareProgramResponse] = None

    class Config:
        from_attributes = True
