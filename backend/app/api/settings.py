from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/preferences", response_model=Dict[str, Any])
def get_settings(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    return {
        "notifications": True,
        "theme": "dark",
        "timezone": "UTC"
    }

@router.put("/preferences", response_model=Dict[str, Any])
def update_settings(
    preferences: Dict[str, Any],
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    return preferences
