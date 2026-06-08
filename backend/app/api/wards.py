from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.ward import Ward
from app.models.patient import Patient

router = APIRouter(prefix="/wards", tags=["wards"])

@router.get("/")
def get_wards(
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    # Mocking the ward aggregate responses for the UI MVP
    wards = db.query(Ward).all()
    result = []
    for ward in wards:
        patients_count = db.query(Patient).filter(Patient.ward_id == ward.id).count()
        critical_count = db.query(Patient).filter(Patient.ward_id == ward.id, Patient.priority == "critical").count()
        
        result.append({
            "id": ward.id,
            "name": ward.name,
            "type": ward.type,
            "total_patients": patients_count,
            "critical_alerts": critical_count,
            "status": "Attention Required" if critical_count > 0 else "Stable"
        })
    
    # If db is empty (mock phase), return demo data
    if not result:
        return [
            {"id": 1, "name": "ICU - Floor 3", "type": "INPATIENT", "total_patients": 12, "critical_alerts": 2, "status": "Attention Required"},
            {"id": 2, "name": "General Ward A", "type": "INPATIENT", "total_patients": 45, "critical_alerts": 0, "status": "Stable"},
            {"id": 3, "name": "Remote Home Monitoring", "type": "HOME_MONITORING", "total_patients": 128, "critical_alerts": 1, "status": "Attention Required"}
        ]
        
    return result
