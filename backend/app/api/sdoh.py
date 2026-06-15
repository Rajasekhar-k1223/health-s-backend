from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/sdoh", tags=["sdoh"])

@router.get("/assessments", response_model=List[Dict[str, Any]])
def get_sdoh_assessments(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return [
        {"patient": "Mason Alvarez", "mrn": "MRN-5512", "housing": "Stable", "food": "Insecure", "transport": "Needs Assistance", "isolation": "High Risk"},
        {"patient": "Priya Shah", "mrn": "MRN-5598", "housing": "Stable", "food": "Secure", "transport": "Owns Vehicle", "isolation": "Low Risk"},
        {"patient": "Owen Reyes", "mrn": "MRN-5471", "housing": "Unstable", "food": "Insecure", "transport": "Needs Assistance", "isolation": "High Risk"}
    ]
