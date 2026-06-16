from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_role, get_current_user
from app.models.user import RoleEnum, User
from app.models.insight import Insight
from app.models.note import DoctorNote
from app.models.patient import Patient
from app.schemas.ai import InsightCreate, InsightResponse, NoteCreate, NoteResponse, PatientRiskSummary

router = APIRouter(prefix="/ai", tags=["ai"])

from fastapi import BackgroundTasks

@router.post("/insights", response_model=InsightResponse)
def create_insight(
    insight_in: InsightCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
    # Internally called by AI service, in production would need service auth
):
    new_insight = Insight(**insight_in.dict())
    db.add(new_insight)
    db.commit()
    db.refresh(new_insight)
    
    from app.services.fhir_sync import sync_risk_assessment
    background_tasks.add_task(sync_risk_assessment, new_insight.id, new_insight.patient_id, new_insight.summary)
    
    return new_insight

@router.get("/patient-insights/{patient_id}", response_model=List[InsightResponse])
def get_patient_insights(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return db.query(Insight).filter(Insight.patient_id == patient_id).order_by(Insight.timestamp.desc()).all()

@router.patch("/insights/{insight_id}/review", response_model=InsightResponse)
def review_insight(
    insight_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor]))
):
    insight = db.query(Insight).filter(Insight.id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    insight.is_reviewed = True
    db.commit()
    db.refresh(insight)
    return insight

@router.post("/notes", response_model=NoteResponse)
def add_doctor_note(
    note_in: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor]))
):
    new_note = DoctorNote(**note_in.dict(), doctor_id=current_user.id)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

@router.get("/patient-summary/{patient_id}", response_model=PatientRiskSummary)
def get_patient_summary(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    recent_insights = db.query(Insight).filter(Insight.patient_id == patient_id).order_by(Insight.timestamp.desc()).limit(5).all()
    recent_notes = db.query(DoctorNote).filter(DoctorNote.patient_id == patient_id).order_by(DoctorNote.timestamp.desc()).limit(5).all()
    
    return PatientRiskSummary(
        patient_id=patient.id,
        overall_risk_score=patient.risk_score,
        priority=patient.priority,
        recent_insights=recent_insights,
        recent_notes=recent_notes
    )

@router.patch("/patient-priority/{patient_id}")
def update_patient_priority(
    patient_id: int,
    priority: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor]))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.priority = priority
    db.commit()
    
    from app.services.fhir_sync import sync_measure_report
    # Score is 1 for testing MeasureReport
    background_tasks.add_task(sync_measure_report, patient.id, patient.id, 1, priority)
    
    return {"status": "success", "priority": priority}
