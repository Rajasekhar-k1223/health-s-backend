import os
import datetime
import requests
from typing import List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.diagnostic_report import DiagnosticReport
from app.models.patient import Patient
from app.services.fhir_sync import sync_diagnostic_report

router = APIRouter(prefix="/labs", tags=["labs"])

class LabOrderCreate(BaseModel):
    patient_id: int
    test_name: str
    priority: str = "routine"

FHIR_URL = os.getenv("FHIR_SERVER_URL", "http://localhost:8080/fhir")

@router.post("/orders")
def create_lab_order(
    order: LabOrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    report = DiagnosticReport(
        patient_id=order.patient_id,
        test_name=order.test_name,
        status="registered"
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # FHIR ServiceRequest for Lab Order
    fhir_payload = {
        "resourceType": "ServiceRequest",
        "id": f"req-{report.id}",
        "status": "active",
        "intent": "order",
        "priority": order.priority,
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "display": order.test_name
                }
            ],
            "text": order.test_name
        },
        "subject": {
            "reference": f"Patient/patient-{order.patient_id}"
        },
        "requester": {
            "reference": f"Practitioner/doctor-{current_user.id}"
        },
        "authoredOn": datetime.datetime.utcnow().isoformat() + "Z"
    }

    try:
        response = requests.put(f"{FHIR_URL}/ServiceRequest/{fhir_payload['id']}", json=fhir_payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to sync ServiceRequest to FHIR: {str(e)}")

    return {"message": "Lab order created successfully", "report_id": report.id, "test_name": order.test_name}

@router.put("/orders/{report_id}/result")
def update_lab_result(
    report_id: int,
    result_value: str,
    conclusion: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse]))
):
    report = db.query(DiagnosticReport).filter(DiagnosticReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.status = "final"
    report.result_value = result_value
    report.conclusion = conclusion
    db.commit()
    
    background_tasks.add_task(sync_diagnostic_report, report.id, report.patient_id, report.test_name, report.result_value, report.conclusion)
    return {"message": "Result updated", "report_id": report.id}

@router.get("/orders", response_model=List[Dict[str, Any]])
def get_lab_orders(
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    reports = db.query(DiagnosticReport).order_by(DiagnosticReport.issued_date.desc()).all()
    return [
        {
            "id": f"LAB-{r.id}", 
            "patient": f"{r.patient.first_name} {r.patient.last_name}" if r.patient else f"Patient {r.patient_id}", 
            "test": r.test_name, 
            "status": r.status, 
            "date": r.issued_date.strftime("%Y-%m-%d") if r.issued_date else "", 
            "result": r.result_value or "—"
        }
        for r in reports
    ]
