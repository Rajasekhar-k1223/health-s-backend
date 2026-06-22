from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User, RoleEnum
from app.models.patient import Patient
from app.models.medical_history import MedicalHistory, HistoryStatusEnum
from app.models.immunization import Immunization
from app.models.family_history import FamilyHistory
from app.models.procedure import Procedure
from app.models.diagnostic_report import DiagnosticReport
from app.services import fhir_sync
from pydantic import BaseModel
import datetime
import random

router = APIRouter(prefix="/patients", tags=["patients"])

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    age: int
    dob: Optional[str] = None
    gender: Optional[str] = None
    contact_number: Optional[str] = None
    address: Optional[str] = None
    primary_doctor_id: Optional[int] = None

class ConditionCreate(BaseModel):
    condition: str
    diagnosed_date: Optional[str] = None
    status: str = "active"
    notes: Optional[str] = None

class ImmunizationCreate(BaseModel):
    vaccine_code: str
    vaccine_name: str
    status: str = "completed"
    notes: Optional[str] = None

class FamilyHistoryCreate(BaseModel):
    relationship_code: str
    condition_name: str
    notes: Optional[str] = None

class ProcedureCreate(BaseModel):
    procedure_code: str
    procedure_name: str
    status: str = "completed"
    notes: Optional[str] = None

class AssignDoctorSchema(BaseModel):
    doctor_id: int

class ReportCreate(BaseModel):
    test_name: str
    conclusion: Optional[str] = None
    result_value: Optional[str] = None
    status: str = "final"

@router.get("/")
def get_patients(
    skip: int = 0, limit: int = 100, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    patients = db.query(Patient).offset(skip).limit(limit).all()
    return patients

@router.get("/doctors/list")
def list_doctors(
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    doctors = db.query(User).filter(User.role.in_([RoleEnum.doctor, RoleEnum.nurse])).all()
    return [{"id": d.id, "first_name": d.first_name, "last_name": d.last_name, "role": d.role} for d in doctors]

@router.post("/")
def create_patient(
    patient_in: PatientCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    parsed_dob = None
    if patient_in.dob:
        try:
            parsed_dob = datetime.datetime.strptime(patient_in.dob, "%Y-%m-%d").date()
        except Exception:
            pass

    # Generate a mock MRN
    mrn = f"MRN-{random.randint(1000000, 9999999)}"

    db_patient = Patient(
        first_name=patient_in.first_name,
        last_name=patient_in.last_name,
        age=patient_in.age,
        dob=parsed_dob,
        gender=patient_in.gender or "other",
        contact_number=patient_in.contact_number,
        address=patient_in.address,
        primary_doctor_id=patient_in.primary_doctor_id or current_user.id,
        mrn=mrn,
        risk_score=0.0,
        priority="low"
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

    # Sync to FHIR in background
    background_tasks.add_task(fhir_sync.sync_patient_to_fhir, db_patient)

    return db_patient

@router.get("/{patient_id}")
def get_patient(
    patient_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    doctor_name = "Unassigned"
    if patient.primary_doctor_id:
        doctor = db.query(User).filter(User.id == patient.primary_doctor_id).first()
        if doctor:
            doctor_name = f"Dr. {doctor.first_name or ''} {doctor.last_name or ''}".strip()
            if not doctor.first_name and not doctor.last_name:
                doctor_name = f"Doctor #{doctor.id}"

    return {
        "id": patient.id,
        "mrn": patient.mrn,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "dob": patient.dob.isoformat() if patient.dob else None,
        "gender": patient.gender,
        "contact_number": patient.contact_number,
        "address": patient.address,
        "age": patient.age,
        "risk_score": patient.risk_score,
        "priority": patient.priority,
        "primary_doctor_id": patient.primary_doctor_id,
        "doctor_name": doctor_name,
        "medical_history": [
            {
                "id": h.id,
                "condition": h.condition,
                "diagnosed_date": h.diagnosed_date.isoformat() if h.diagnosed_date else None,
                "status": h.status,
                "notes": h.notes
            } for h in patient.medical_history
        ],
        "immunizations": [
            {
                "id": i.id,
                "vaccine_code": i.vaccine_code,
                "vaccine_name": i.vaccine_name,
                "administered_date": i.administered_date.isoformat() if i.administered_date else None,
                "status": i.status,
                "notes": i.notes
            } for i in patient.immunizations
        ],
        "family_histories": [
            {
                "id": f.id,
                "relationship_code": f.relationship_code,
                "condition_name": f.condition_name,
                "notes": f.notes
            } for f in patient.family_histories
        ],
        "procedures": [
            {
                "id": p.id,
                "procedure_code": p.procedure_code,
                "procedure_name": p.procedure_name,
                "status": p.status,
                "notes": p.notes
            } for p in patient.procedures
        ],
        "reports": [
            {
                "id": r.id,
                "test_name": r.test_name,
                "status": r.status,
                "conclusion": r.conclusion,
                "result_value": r.result_value,
                "issued_date": r.issued_date.isoformat() if r.issued_date else None
            } for r in db.query(DiagnosticReport).filter(DiagnosticReport.patient_id == patient_id).all()
        ],
        "encounters": [
            {
                "id": e.id,
                "status": e.status,
                "encounter_class": e.encounter_class,
                "start_time": e.start_time.isoformat() if e.start_time else None,
                "end_time": e.end_time.isoformat() if e.end_time else None,
                "reason": e.reason
            } for e in patient.encounters
        ]
    }

@router.post("/{patient_id}/assign-doctor")
def assign_doctor(
    patient_id: int,
    schema: AssignDoctorSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    doctor = db.query(User).filter(User.id == schema.doctor_id).first()
    if not doctor or doctor.role not in [RoleEnum.doctor, RoleEnum.nurse]:
        raise HTTPException(status_code=400, detail="Invalid doctor ID")
        
    patient.primary_doctor_id = schema.doctor_id
    db.commit()
    db.refresh(patient)
    
    background_tasks.add_task(fhir_sync.sync_patient_to_fhir, patient)
    
    return {"message": "Doctor assigned successfully", "primary_doctor_id": patient.primary_doctor_id}

@router.get("/{patient_id}/history")
def get_medical_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    history = db.query(MedicalHistory).filter(MedicalHistory.patient_id == patient_id).all()
    return history

@router.post("/{patient_id}/history")
def add_condition(
    patient_id: int,
    cond_in: ConditionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse]))
):
    parsed_date = None
    if cond_in.diagnosed_date:
        try:
            parsed_date = datetime.datetime.strptime(cond_in.diagnosed_date, "%Y-%m-%d").date()
        except Exception:
            pass

    db_history = MedicalHistory(
        patient_id=patient_id,
        condition=cond_in.condition,
        diagnosed_date=parsed_date,
        status=HistoryStatusEnum(cond_in.status),
        notes=cond_in.notes
    )
    db.add(db_history)
    db.commit()
    db.refresh(db_history)

    background_tasks.add_task(fhir_sync.sync_condition, db_history.id, patient_id, cond_in.condition, cond_in.status)

    return db_history

@router.post("/{patient_id}/immunizations")
def add_immunization(
    patient_id: int,
    imm_in: ImmunizationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse]))
):
    db_imm = Immunization(
        patient_id=patient_id,
        vaccine_code=imm_in.vaccine_code,
        vaccine_name=imm_in.vaccine_name,
        status=imm_in.status,
        notes=imm_in.notes
    )
    db.add(db_imm)
    db.commit()
    db.refresh(db_imm)

    background_tasks.add_task(fhir_sync.sync_immunization, db_imm.id, patient_id, imm_in.vaccine_code, imm_in.vaccine_name, imm_in.status)

    return db_imm

@router.post("/{patient_id}/family-history")
def add_family_history(
    patient_id: int,
    fh_in: FamilyHistoryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse]))
):
    db_fh = FamilyHistory(
        patient_id=patient_id,
        relationship_code=fh_in.relationship_code,
        condition_name=fh_in.condition_name,
        notes=fh_in.notes
    )
    db.add(db_fh)
    db.commit()
    db.refresh(db_fh)

    background_tasks.add_task(fhir_sync.sync_family_history, db_fh.id, patient_id, fh_in.relationship_code, fh_in.condition_name)

    return db_fh

@router.post("/{patient_id}/procedures")
def add_procedure(
    patient_id: int,
    proc_in: ProcedureCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse]))
):
    db_proc = Procedure(
        patient_id=patient_id,
        procedure_code=proc_in.procedure_code,
        procedure_name=proc_in.procedure_name,
        status=proc_in.status,
        notes=proc_in.notes
    )
    db.add(db_proc)
    db.commit()
    db.refresh(db_proc)

    background_tasks.add_task(fhir_sync.sync_procedure, db_proc.id, patient_id, proc_in.procedure_code, proc_in.procedure_name, proc_in.status)

    return db_proc

@router.get("/{patient_id}/reports")
def get_reports(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    reports = db.query(DiagnosticReport).filter(DiagnosticReport.patient_id == patient_id).all()
    return reports

@router.post("/{patient_id}/reports")
def add_report(
    patient_id: int,
    report_in: ReportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse]))
):
    db_report = DiagnosticReport(
        patient_id=patient_id,
        test_name=report_in.test_name,
        conclusion=report_in.conclusion,
        result_value=report_in.result_value,
        status=report_in.status
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    background_tasks.add_task(fhir_sync.sync_diagnostic_report, db_report.id, patient_id, report_in.test_name, report_in.result_value, report_in.conclusion)

    return db_report
