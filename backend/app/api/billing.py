from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/billing", tags=["billing"])

@router.get("/claims", response_model=List[Dict[str, Any]])
def get_billing_claims(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return [
        {"id": "CLM-8901", "patient": "Mason Alvarez", "amount": "$1,250.00", "status": "Paid", "date": "2026-06-01", "payer": "Medicare"},
        {"id": "CLM-8902", "patient": "Priya Shah", "amount": "$450.00", "status": "Pending", "date": "2026-06-05", "payer": "BlueCross"},
        {"id": "CLM-8903", "patient": "Owen Reyes", "amount": "$3,100.00", "status": "Denied", "date": "2026-05-28", "payer": "Aetna"},
        {"id": "CLM-8904", "patient": "Lina Karis", "amount": "$120.00", "status": "Paid", "date": "2026-06-02", "payer": "Cigna"}
    ]
