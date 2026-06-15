from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/compliance", tags=["compliance"])

@router.get("/audits", response_model=List[Dict[str, Any]])
def get_compliance_audits(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return [
        {"requirement": "HIPAA Privacy Rule", "status": "Compliant", "lastChecked": "2026-06-08", "score": 98},
        {"requirement": "SOC 2 Type II", "status": "Compliant", "lastChecked": "2026-06-01", "score": 100},
        {"requirement": "GDPR Data Processing", "status": "Review Needed", "lastChecked": "2026-05-15", "score": 85},
        {"requirement": "HITECH Act", "status": "Compliant", "lastChecked": "2026-06-05", "score": 95}
    ]
