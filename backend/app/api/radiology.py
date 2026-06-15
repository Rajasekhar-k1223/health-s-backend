from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/radiology", tags=["radiology"])

@router.get("/studies", response_model=List[Dict[str, Any]])
def get_radiology_studies(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return [
        {"id": "IMG-501", "patient": "Mason Alvarez", "modality": "CT Scan - Chest", "status": "Report Available", "date": "2026-06-08", "urgency": "Routine"},
        {"id": "IMG-502", "patient": "Priya Shah", "modality": "MRI - Brain", "status": "In Progress", "date": "2026-06-09", "urgency": "Stat"},
        {"id": "IMG-503", "patient": "Owen Reyes", "modality": "X-Ray - Chest", "status": "Report Available", "date": "2026-06-09", "urgency": "Stat"},
        {"id": "IMG-504", "patient": "Eli Johansen", "modality": "Ultrasound - Abdomen", "status": "Scheduled", "date": "2026-06-10", "urgency": "Routine"}
    ]
