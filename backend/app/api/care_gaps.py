from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/care-gaps", tags=["care-gaps"])

@router.get("/measures", response_model=List[Dict[str, Any]])
def get_care_gaps(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return [
        {"measure": "Colorectal Cancer Screening", "population": 1450, "compliant": 890, "pct": 61, "target": 80},
        {"measure": "HbA1c Control (< 8.0%)", "population": 820, "compliant": 510, "pct": 62, "target": 75},
        {"measure": "Breast Cancer Screening", "population": 1200, "compliant": 840, "pct": 70, "target": 81},
        {"measure": "Statin Therapy for CVD", "population": 950, "compliant": 820, "pct": 86, "target": 85}
    ]
