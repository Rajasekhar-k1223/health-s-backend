from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/medications", tags=["medications"])

@router.get("/adherence", response_model=Dict[str, Any])
def get_medication_adherence(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    return {
        "watchlist": [
            { "name": "Mason Alvarez", "mrn": "MRN-5512", "drug": "Carvedilol 12.5mg", "missed": 3, "period": "7 days", "lastTook": "18h ago", "adherence": 57, "status": "Critical" },
            { "name": "Priya Shah", "mrn": "MRN-5598", "drug": "Lisinopril 20mg", "missed": 0, "period": "refill 6d overdue", "lastTook": "on time", "adherence": 78, "status": "Refill Due" },
            { "name": "Owen Reyes", "mrn": "MRN-5471", "drug": "Furosemide 40mg", "missed": 0, "period": "4 late doses", "lastTook": "4h late", "adherence": 84, "status": "Watch" },
            { "name": "Eli Johansen", "mrn": "MRN-5404", "drug": "Metformin 1000mg", "missed": 0, "period": "30 days", "lastTook": "on time", "adherence": 92, "status": "On Track" },
            { "name": "Lina Karis", "mrn": "MRN-5480", "drug": "Atorvastatin 40mg", "missed": 1, "period": "7 days", "lastTook": "2d ago", "adherence": 70, "status": "Watch" },
            { "name": "Sara Vela", "mrn": "MRN-5390", "drug": "Apixaban 5mg", "missed": 0, "period": "7 days", "lastTook": "this morning", "adherence": 100, "status": "On Track" }
        ],
        "top_meds": [
            ["Atorvastatin", 412, 91],
            ["Lisinopril", 318, 87],
            ["Metformin", 284, 89],
            ["Carvedilol", 196, 72],
            ["Apixaban", 141, 94],
            ["Levothyroxine", 128, 88],
            ["Amlodipine", 112, 85]
        ]
    }
