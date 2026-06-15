from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/risk", tags=["risk"])

@router.get("/patients", response_model=List[Dict[str, Any]])
def get_risk_patients(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return [
        {"patient": "Mason Alvarez", "mrn": "MRN-5512", "score": 92, "trend": "+4", "category": "High Risk", "drivers": ["Heart Failure", "Low Adherence", "Age > 65"]},
        {"patient": "Priya Shah", "mrn": "MRN-5598", "score": 78, "trend": "-2", "category": "Medium Risk", "drivers": ["Hypertension", "Recent ER Visit"]},
        {"patient": "Owen Reyes", "mrn": "MRN-5471", "score": 85, "trend": "+12", "category": "High Risk", "drivers": ["Abnormal Telemetry", "COPD"]},
        {"patient": "Lina Karis", "mrn": "MRN-5480", "score": 45, "trend": "0", "category": "Low Risk", "drivers": ["Stable vitals"]}
    ]
