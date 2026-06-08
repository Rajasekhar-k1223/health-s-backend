from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import datetime

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.patient import Patient
from app.models.audit import AuditLog

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/generate")
def generate_report(
    report_type: str, # PATIENT, DEVICE, COMPLIANCE
    format: str = "CSV",
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    """
    Simulates generating a report and exporting it as CSV/PDF.
    """
    if report_type == "PATIENT":
        count = db.query(Patient).count()
        data = f"Total Patients: {count}"
    elif report_type == "COMPLIANCE":
        count = db.query(AuditLog).count()
        data = f"Total Audit Events: {count}"
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")
        
    return {
        "report_id": f"REP-{datetime.datetime.now().timestamp()}",
        "type": report_type,
        "format": format,
        "status": "COMPLETED",
        "download_url": f"/api/v1/exports/download?id=REP-12345",
        "preview_data": data
    }
