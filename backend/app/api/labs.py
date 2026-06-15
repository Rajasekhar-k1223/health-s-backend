from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/labs", tags=["labs"])

@router.get("/orders", response_model=List[Dict[str, Any]])
def get_lab_orders(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return [
        {"id": "LAB-101", "patient": "Mason Alvarez", "test": "Comprehensive Metabolic Panel", "status": "Completed", "date": "2026-06-08", "result": "Normal"},
        {"id": "LAB-102", "patient": "Priya Shah", "test": "Lipid Panel", "status": "Pending", "date": "2026-06-09", "result": "—"},
        {"id": "LAB-103", "patient": "Owen Reyes", "test": "Troponin I", "status": "Completed", "date": "2026-06-09", "result": "Elevated"},
        {"id": "LAB-104", "patient": "Eli Johansen", "test": "HbA1c", "status": "Completed", "date": "2026-06-05", "result": "Abnormal (8.2%)"}
    ]
