from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/locations", tags=["locations"])

@router.get("/", response_model=List[Dict[str, Any]])
def get_locations(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return [
        {"name": "Sentinel Main Hospital", "type": "Hospital", "address": "123 Healthcare Blvd", "status": "Active"},
        {"name": "Northside Urgent Care", "type": "Clinic", "address": "450 North Ave", "status": "Active"},
        {"name": "West End Pharmacy", "type": "Pharmacy", "address": "980 West St", "status": "Active"}
    ]
