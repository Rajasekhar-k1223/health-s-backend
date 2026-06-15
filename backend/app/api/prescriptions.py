from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])

# In-memory mock DB for prescriptions
MOCK_RX = [
    { "id": 1, "patient": "Mason Alvarez", "mrn": "MRN-5512", "drug": "Carvedilol 12.5mg", "sig": "BID with food", "prescriber": "Dr. Mehta", "date": "2026-06-01", "refills": 2, "status": "Active" },
    { "id": 2, "patient": "Priya Shah", "mrn": "MRN-5598", "drug": "Lisinopril 20mg", "sig": "Once daily", "prescriber": "Dr. Shah", "date": "2026-05-28", "refills": 3, "status": "Active" },
    { "id": 3, "patient": "Owen Reyes", "mrn": "MRN-5471", "drug": "Furosemide 40mg", "sig": "Once daily AM", "prescriber": "Dr. Reyes", "date": "2026-05-15", "refills": 1, "status": "Refill Due" },
    { "id": 4, "patient": "Eli Johansen", "mrn": "MRN-5404", "drug": "Metformin 1000mg", "sig": "BID with meals", "prescriber": "Dr. Mehta", "date": "2026-06-05", "refills": 5, "status": "Active" },
    { "id": 5, "patient": "Sara Vela", "mrn": "MRN-5390", "drug": "Atorvastatin 40mg", "sig": "Once daily at night", "prescriber": "Dr. Shah", "date": "2026-04-10", "refills": 0, "status": "Expired" }
]

@router.get("/", response_model=List[Dict[str, Any]])
def get_prescriptions(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    return MOCK_RX

@router.post("/", response_model=Dict[str, Any])
def create_prescription(
    prescription: Dict[str, Any],
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor]))
):
    new_rx = {
        "id": len(MOCK_RX) + 1,
        "patient": prescription.get("patient"),
        "mrn": prescription.get("mrn", "MRN-NEW"),
        "drug": prescription.get("drug"),
        "sig": prescription.get("sig"),
        "prescriber": current_user.username,
        "date": "2026-06-09",
        "refills": int(prescription.get("refills", 0)),
        "status": "Active"
    }
    MOCK_RX.insert(0, new_rx)
    return new_rx
