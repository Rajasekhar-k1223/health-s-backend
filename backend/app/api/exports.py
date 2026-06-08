from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
import os
import csv
import json
import datetime

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.patient import Patient
from app.models.audit import AuditLog

router = APIRouter(prefix="/exports", tags=["exports"])

EXPORT_DIR = "/tmp/sentinel_exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

def generate_csv_export(file_path: str, db: Session):
    patients = db.query(Patient).all()
    with open(file_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "First Name", "Last Name", "DOB"])
        for p in patients:
            writer.writerow([p.id, p.first_name, p.last_name, p.dob])

def generate_fhir_export(file_path: str, db: Session):
    patients = db.query(Patient).all()
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": []
    }
    for p in patients:
        bundle["entry"].append({
            "resource": {
                "resourceType": "Patient",
                "id": str(p.id),
                "name": [{"family": p.last_name, "given": [p.first_name]}]
            }
        })
    with open(file_path, 'w') as f:
        json.dump(bundle, f)

@router.post("/request")
def request_export(
    export_type: str, # PATIENT, AUDIT
    format: str = "CSV", # CSV, PDF, EXCEL, FHIR
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    export_id = f"EXP-{int(datetime.datetime.now().timestamp())}"
    file_name = f"{export_id}.{format.lower()}"
    file_path = os.path.join(EXPORT_DIR, file_name)
    
    if format == "CSV":
        background_tasks.add_task(generate_csv_export, file_path, db)
    elif format == "FHIR":
        background_tasks.add_task(generate_fhir_export, file_path, db)
    else:
        raise HTTPException(status_code=400, detail="Format not supported for this type yet")
        
    return {"export_id": export_id, "status": "PROCESSING", "download_url": f"/api/v1/exports/download/{export_id}"}

@router.get("/download/{export_id}")
def download_export(
    export_id: str,
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    # Search for the file in the export dir
    for ext in ["csv", "json", "pdf", "xlsx"]:
        file_path = os.path.join(EXPORT_DIR, f"{export_id}.{ext}")
        if os.path.exists(file_path):
            return FileResponse(file_path, filename=f"{export_id}.{ext}")
            
    raise HTTPException(status_code=404, detail="Export not found or still processing")
