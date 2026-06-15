from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/equity", tags=["equity"])

@router.get("/metrics", response_model=Dict[str, Any])
def get_equity_metrics(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return {
        "index": "8.4/10",
        "readmission_disparity": "2.1%",
        "demographic_coverage": "98%",
        "active_interventions": 12
    }
