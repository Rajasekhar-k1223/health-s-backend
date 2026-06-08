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
    current_user = Depends(require_role([RoleEnum.admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return db.query(Patient).offset(skip).limit(limit).all()

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.admin, RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
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
    current_user = Depends(require_role([RoleEnum.admin, RoleEnum.doctor, RoleEnum.nurse]))
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
