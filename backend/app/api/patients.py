from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.patient import Patient
from app.models.insight import Insight
from app.schemas.patient import PatientCreate, PatientResponse, MedicalHistoryCreate, MedicalHistoryResponse
from app.models.medical_history import MedicalHistory
from app.services.fhir_sync import sync_patient_to_fhir
import uuid

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/", response_model=PatientResponse)
def create_patient(
    patient_in: PatientCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor]))
):
    patient_data = patient_in.dict()
    if not patient_data.get("mrn"):
        patient_data["mrn"] = f"MRN-{uuid.uuid4().hex[:8].upper()}"
        
    new_patient = Patient(**patient_data)
    
    # Enforce Multi-Tenant Data Governance: Tie patient to current user's organization
    if current_user.role != RoleEnum.super_admin:
        new_patient.organization_id = current_user.organization_id
        
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    
    # Trigger asynchronous FHIR synchronization
    background_tasks.add_task(sync_patient_to_fhir, new_patient)
    
    return new_patient

@router.get("/", response_model=List[PatientResponse])
def get_patients(
    skip: int = 0, limit: int = 100, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    query = db.query(Patient)
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin:
        query = query.filter(Patient.organization_id == current_user.organization_id)
        
    return query.offset(skip).limit(limit).all()

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin and current_user.role != RoleEnum.patient:
        if patient.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Patient does not belong to your organization")

    # If the user is a patient, they can only view their own record
    if current_user.role == RoleEnum.patient and patient.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions to view this patient")

    return patient

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    patient_in: PatientCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor]))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin:
        if patient.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Patient does not belong to your organization")
        
    for key, value in patient_in.dict(exclude_unset=True).items():
        setattr(patient, key, value)
        
    db.commit()
    db.refresh(patient)
    
    background_tasks.add_task(sync_patient_to_fhir, patient)
    return patient

@router.post("/{patient_id}/history", response_model=MedicalHistoryResponse)
def add_medical_history(
    patient_id: int,
    history_in: MedicalHistoryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse]))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    new_history = MedicalHistory(**history_in.dict(), patient_id=patient_id)
    db.add(new_history)
    db.commit()
    db.refresh(new_history)
    
    from app.services.fhir_sync import sync_condition
    background_tasks.add_task(sync_condition, new_history.id, patient_id, new_history.condition, new_history.status.value)
    
    return new_history

@router.get("/{patient_id}/history", response_model=List[MedicalHistoryResponse])
def get_medical_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    return db.query(MedicalHistory).filter(MedicalHistory.patient_id == patient_id).all()

@router.get("/{patient_id}/360")
def get_patient_360(
    patient_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    latest_insight = db.query(Insight).filter(Insight.patient_id == patient_id).order_by(Insight.timestamp.desc()).first()
    
    if latest_insight:
        insight_dict = {
            "risk_score": latest_insight.score,
            "risk_level": "Critical" if latest_insight.score > 80 else "High" if latest_insight.score > 60 else "Medium" if latest_insight.score > 30 else "Low",
            "summary": latest_insight.summary
        }
    else:
        insight_dict = {
            "risk_score": 0,
            "risk_level": "Pending",
            "summary": "No AI insights generated yet. This is not a diagnosis. Clinical review is recommended."
        }
        
    return {
        "patient": {
            "id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "dob": "1980-01-01", # Mocked
            "gender": "Unknown", # Mocked
            "blood_type": "Unknown", # Mocked
            "mrn": f"MRN-{patient.id}",
            "ward_id": patient.ward_id
        },
        "live_vitals": {
            "heart_rate": 82,
            "spo2": 98,
            "temperature": 98.6,
            "respiration_rate": 16,
            "timestamp": "2023-10-26T15:35:00Z"
        },
        "ai_insights": insight_dict,
        "recent_documents": [
            {
                "id": "DOC-102",
                "type": "Lab Report",
                "date": "2023-10-25",
                "findings": ["Normal CBC", "Slightly elevated LDL"]
            },
            {
                "id": "DOC-103",
                "type": "Discharge Summary",
                "date": "2022-04-12",
                "findings": ["Recovered from mild pneumonia."]
            }
        ],
        "timeline_events": [
            {"date": "2023-10-26T10:00:00Z", "type": "VitalsAlert", "description": "Heart rate spiked to 110 BPM. Resolved."}
        ]
    }

from pydantic import BaseModel
class ConsentCreate(BaseModel):
    category: str = "hipaa-notice"
    policy_rule: str = "http://sentinel-health.os/privacy-policy"
    provision_type: str = "permit"

@router.post("/{patient_id}/consent")
def create_patient_consent(
    patient_id: int,
    consent_in: ConsentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.patient]))
):
    from app.models.consent import Consent
    
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    consent = Consent(
        patient_id=patient_id,
        organization_id=patient.organization_id,
        category=consent_in.category,
        policy_rule=consent_in.policy_rule,
        provision_type=consent_in.provision_type
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    
    from app.services.fhir_sync import sync_consent
    background_tasks.add_task(sync_consent, consent.id, patient_id, consent.organization_id, consent.status.value, consent.provision_type)
    
    return consent

class ImmunizationCreate(BaseModel):
    vaccine_code: str
    vaccine_name: str
    status: str = "completed"
    notes: str = None

@router.post("/{patient_id}/immunizations")
def create_patient_immunization(
    patient_id: int,
    imm_in: ImmunizationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse]))
):
    from app.models.immunization import Immunization
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient not found")
        
    imm = Immunization(
        patient_id=patient_id,
        vaccine_code=imm_in.vaccine_code,
        vaccine_name=imm_in.vaccine_name,
        status=imm_in.status,
        notes=imm_in.notes
    )
    db.add(imm)
    db.commit()
    db.refresh(imm)
    
    from app.services.fhir_sync import sync_immunization
    background_tasks.add_task(sync_immunization, imm.id, patient_id, imm.vaccine_code, imm.vaccine_name, imm.status)
    return imm

class FamilyHistoryCreate(BaseModel):
    relationship_code: str
    condition_name: str
    notes: str = None

@router.post("/{patient_id}/family-history")
def create_patient_family_history(
    patient_id: int,
    fh_in: FamilyHistoryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse]))
):
    from app.models.family_history import FamilyHistory
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient not found")
        
    fh = FamilyHistory(
        patient_id=patient_id,
        relationship_code=fh_in.relationship_code,
        condition_name=fh_in.condition_name,
        notes=fh_in.notes
    )
    db.add(fh)
    db.commit()
    db.refresh(fh)
    
    from app.services.fhir_sync import sync_family_history
    background_tasks.add_task(sync_family_history, fh.id, patient_id, fh.relationship_code, fh.condition_name)
    return fh

class ProcedureCreate(BaseModel):
    procedure_code: str
    procedure_name: str
    status: str = "completed"
    notes: str = None

@router.post("/{patient_id}/procedures")
def create_patient_procedure(
    patient_id: int,
    proc_in: ProcedureCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse]))
):
    from app.models.procedure import Procedure
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient not found")
        
    proc = Procedure(
        patient_id=patient_id,
        procedure_code=proc_in.procedure_code,
        procedure_name=proc_in.procedure_name,
        status=proc_in.status,
        notes=proc_in.notes
    )
    db.add(proc)
    db.commit()
    db.refresh(proc)
    
    from app.services.fhir_sync import sync_procedure
    background_tasks.add_task(sync_procedure, proc.id, patient_id, proc.procedure_code, proc.procedure_name, proc.status)
    return proc
