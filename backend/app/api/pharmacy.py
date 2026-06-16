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
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from fastapi import BackgroundTasks, HTTPException
from app.models.patient import Patient

class MedDispenseCreate(BaseModel):
    patient_id: int
    medication_name: str
    quantity: str
    days_supply: int
    status: str = "completed"
    notes: str = None

@router.post("/dispense")
def create_medication_dispense(
    dispense_in: MedDispenseCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.doctor, RoleEnum.nurse, RoleEnum.hospital_admin]))
):
    from app.models.medication_dispense import MedicationDispense
    patient = db.query(Patient).filter(Patient.id == dispense_in.patient_id).first()
    if not patient: raise HTTPException(status_code=404, detail="Patient not found")
        
    med_dispense = MedicationDispense(
        patient_id=dispense_in.patient_id,
        medication_name=dispense_in.medication_name,
        quantity=dispense_in.quantity,
        days_supply=dispense_in.days_supply,
        status=dispense_in.status,
        notes=dispense_in.notes
    )
    db.add(med_dispense)
    db.commit()
    db.refresh(med_dispense)
    
    from app.services.fhir_sync import sync_medication_dispense
    background_tasks.add_task(sync_medication_dispense, med_dispense.id, med_dispense.patient_id, med_dispense.medication_name, med_dispense.status, med_dispense.quantity, med_dispense.days_supply)
    return med_dispense
