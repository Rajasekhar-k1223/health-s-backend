from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.patient import Patient
from app.models.medical_history import MedicalHistory

router = APIRouter(prefix="/care-gaps", tags=["care-gaps"])

@router.get("/measures", response_model=List[Dict[str, Any]])
def get_care_gaps(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse])),
    db: Session = Depends(get_db)
):
    # 1. Hypertension Care Gap
    htn_population = db.query(MedicalHistory).filter(MedicalHistory.condition.like("%Hypertension%")).count()
    htn_compliant = int(htn_population * 0.65) # Simulate 65% compliance (BP measured recently)
    htn_pct = int((htn_compliant / htn_population * 100)) if htn_population > 0 else 0
    
    # 2. Diabetes Management Gap (HbA1c)
    dm_population = db.query(MedicalHistory).filter(MedicalHistory.condition.like("%Type 2 Diabetes%")).count()
    dm_compliant = int(dm_population * 0.52) # Simulate 52% compliance (HbA1c < 8.0)
    dm_pct = int((dm_compliant / dm_population * 100)) if dm_population > 0 else 0
    
    # 3. Preventive Screening (Age > 50)
    older_population = db.query(Patient).filter(Patient.age > 50).count()
    older_compliant = int(older_population * 0.78) # Simulate 78% compliance
    older_pct = int((older_compliant / older_population * 100)) if older_population > 0 else 0

    return [
        {"measure": "Hypertension Control (< 140/90)", "population": htn_population, "compliant": htn_compliant, "pct": htn_pct, "target": 80},
        {"measure": "HbA1c Control (< 8.0%)", "population": dm_population, "compliant": dm_compliant, "pct": dm_pct, "target": 75},
        {"measure": "Preventative Screening (Age > 50)", "population": older_population, "compliant": older_compliant, "pct": older_pct, "target": 85}
    ]
