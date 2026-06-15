from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum, User
from app.models.chronic_care import CareProgram, ProgramEnrollment
from app.schemas.chronic_care import CareProgramCreate, CareProgramResponse, EnrollmentCreate, EnrollmentResponse, EnrollmentUpdate

router = APIRouter(prefix="/ccm", tags=["chronic_care"])

@router.post("/programs", response_model=CareProgramResponse)
def create_program(
    program_in: CareProgramCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor]))
):
    new_program = CareProgram(**program_in.dict())
    db.add(new_program)
    db.commit()
    db.refresh(new_program)
    return new_program

@router.get("/programs", response_model=List[CareProgramResponse])
def get_programs(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return db.query(CareProgram).offset(skip).limit(limit).all()

@router.post("/enroll", response_model=EnrollmentResponse)
def enroll_patient(
    enrollment_in: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor]))
):
    # Check if already enrolled in this specific program
    existing = db.query(ProgramEnrollment).filter(
        ProgramEnrollment.patient_id == enrollment_in.patient_id,
        ProgramEnrollment.program_id == enrollment_in.program_id,
        ProgramEnrollment.status == "active"
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Patient already actively enrolled in this program")
        
    new_enrollment = ProgramEnrollment(**enrollment_in.dict())
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    return new_enrollment

@router.get("/patient/{patient_id}", response_model=List[EnrollmentResponse])
def get_patient_enrollments(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    return db.query(ProgramEnrollment).filter(ProgramEnrollment.patient_id == patient_id).all()

@router.patch("/enrollment/{enrollment_id}", response_model=EnrollmentResponse)
def update_enrollment(
    enrollment_id: int,
    update_data: EnrollmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    enrollment = db.query(ProgramEnrollment).filter(ProgramEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
        
    if update_data.status:
        enrollment.status = update_data.status
    if update_data.adherence_score is not None:
        enrollment.adherence_score = update_data.adherence_score
        
    db.commit()
    db.refresh(enrollment)
    return enrollment
