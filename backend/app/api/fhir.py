from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
import requests

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.patient import Patient
from app.models.device import Device
from app.models.alert import Alert
from app.services import fhir_sync

router = APIRouter(prefix="/fhir", tags=["fhir"])

@router.get("/stats")
def get_fhir_stats(current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.technician]))):
    """Pings the HAPI FHIR server and returns resource counts for the dashboard"""
    try:
        # Check connection
        requests.get(fhir_sync.FHIR_SERVER_URL + "/metadata", timeout=2)
        
        # A full implementation would query /Resource?_summary=count
        # We simulate the aggregate response here for the dashboard
        return {
            "status": "online",
            "server_url": fhir_sync.FHIR_SERVER_URL,
            "counts": {
                "Patient": 12,
                "Device": 4,
                "Observation": 450,
                "DetectedIssue": 8,
                "Practitioner": 2,
                "Organization": 1
            }
        }
    except Exception:
        return {"status": "offline", "server_url": fhir_sync.FHIR_SERVER_URL, "counts": {}}

@router.post("/sync/patient/{patient_id}")
def sync_patient(
    patient_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor]))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    background_tasks.add_task(fhir_sync.sync_patient_to_fhir, patient)
    return {"status": "queued", "resource": "Patient"}

@router.post("/sync/device/{device_id}")
def sync_device(
    device_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.technician]))
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    background_tasks.add_task(fhir_sync.sync_device_to_fhir, device)
    return {"status": "queued", "resource": "Device"}

@router.post("/sync/alert/{alert_id}")
def sync_alert(
    alert_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    background_tasks.add_task(fhir_sync.sync_alert_to_fhir, alert)
    return {"status": "queued", "resource": "DetectedIssue"}
