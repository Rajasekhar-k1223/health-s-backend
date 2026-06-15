from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])

@router.get("/queue", response_model=List[Dict[str, Any]])
def get_pharmacy_queue(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return [
        {"id": "RX-1001", "patient": "Mason Alvarez", "drug": "Carvedilol 12.5mg", "type": "New Rx", "status": "Dispensing", "time": "10 min ago"},
        {"id": "RX-1002", "patient": "Priya Shah", "drug": "Lisinopril 20mg", "type": "Refill", "status": "Ready", "time": "1 hr ago"},
        {"id": "RX-1003", "patient": "Owen Reyes", "drug": "Furosemide 40mg", "type": "Refill", "status": "Pending Verification", "time": "5 min ago"}
    ]
