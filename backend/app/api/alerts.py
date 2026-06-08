from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum, User
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertResponse, AlertResolve
from app.services.alert_ai import generate_ai_insight

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/", response_model=List[AlertResponse])
def get_all_alerts(
    status: Optional[str] = None, # 'active' or 'resolved'
    skip: int = 0, limit: int = 100, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    query = db.query(Alert)
    if status == 'active':
        query = query.filter(Alert.is_resolved == False)
    elif status == 'resolved':
        query = query.filter(Alert.is_resolved == True)
        
    return query.order_by(Alert.timestamp.desc()).offset(skip).limit(limit).all()

@router.get("/patient/{patient_id}", response_model=List[AlertResponse])
def get_patient_alerts(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return db.query(Alert).filter(Alert.patient_id == patient_id).order_by(Alert.timestamp.desc()).all()

@router.post("/", response_model=AlertResponse)
def create_alert(
    alert_in: AlertCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
    # Internally called by Telemetry Gateway
):
    new_alert = Alert(**alert_in.dict())
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    
    # Trigger Async AI Risk Scoring
    background_tasks.add_task(generate_ai_insight, new_alert.id)
    
    return new_alert

@router.put("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert.is_acknowledged = True
    alert.acknowledged_by = current_user.id
    db.commit()
    db.refresh(alert)
    return alert

@router.put("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: int,
    resolve_in: AlertResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert.is_resolved = True
    alert.resolved_by = current_user.id
    alert.resolved_at = datetime.utcnow()
    alert.resolution_notes = resolve_in.resolution_notes
    db.commit()
    db.refresh(alert)
    return alert
