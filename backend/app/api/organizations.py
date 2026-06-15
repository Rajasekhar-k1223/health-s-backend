from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.get("/", response_model=List[Dict[str, Any]])
def get_organizations(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return [
        {
            "id": "ORG-1",
            "name": "Sentinel Health Network",
            "address": "123 Healthcare Blvd, Medical City",
            "npi": "1234567890",
            "status": "Active"
        }
    ]
