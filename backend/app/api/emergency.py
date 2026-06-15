from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/emergency", tags=["emergency"])

@router.get("/incoming", response_model=List[Dict[str, Any]])
def get_emergency_incoming(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return [
        {"eta": "5 min", "type": "Trauma - MVA", "priority": "Code Red", "unit": "Medic 14", "status": "In Transit"},
        {"eta": "12 min", "type": "Cardiac Arrest", "priority": "Code Blue", "unit": "Medic 9", "status": "In Transit"},
        {"eta": "Arrived", "type": "Stroke Protocol", "priority": "Code Red", "unit": "Walk-in", "status": "Triage"}
    ]
