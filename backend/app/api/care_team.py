from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.care_team import CareTeam

router = APIRouter(prefix="/care-team", tags=["care-team"])

@router.get("/{patient_id}")
def get_patient_care_team(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.doctor, RoleEnum.nurse, RoleEnum.nurse]))
):
    team_members = db.query(CareTeam).filter(CareTeam.patient_id == patient_id).all()
    
    if not team_members:
        # Return mock data for MVP
        return [
            {"id": 1, "name": "Dr. Sarah Jenkins", "role": "Primary Physician", "contact": "Ext 402"},
            {"id": 2, "name": "Mark Evans", "role": "Home Caregiver", "contact": "555-0192"}
        ]
        
    result = []
    for member in team_members:
        result.append({
            "id": member.id,
            "user_id": member.user_id,
            "role": member.role
        })
    return result
