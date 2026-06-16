from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
import requests
from datetime import datetime

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.prescription import Prescription

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])

FHIR_URL = "http://localhost:8080/fhir"

class PrescriptionCreate(BaseModel):
    patient: str = None
    mrn: str = None
    patient_id: int = None
    drug_name: str = None
    drug: str = None
    sig: str
    refills: int = 0

@router.get("/", response_model=List[Dict[str, Any]])
def get_prescriptions(
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    # Depending on role, we would filter here. For now, fetch all or related.
    prescriptions = db.query(Prescription).order_by(Prescription.date_prescribed.desc()).all()
    
    result = []
    for rx in prescriptions:
        result.append({
            "id": rx.id,
            "patient": f"{rx.patient.first_name} {rx.patient.last_name}",
            "mrn": rx.patient.mrn,
            "drug": rx.drug_name,
            "sig": rx.sig,
            "prescriber": f"Dr. {rx.prescriber.first_name} {rx.prescriber.last_name}" if rx.prescriber.first_name else rx.prescriber.username,
            "date": rx.date_prescribed.strftime("%Y-%m-%d"),
            "refills": rx.refills,
            "status": rx.status.value
        })
    return result

@router.post("/", response_model=Dict[str, Any])
def create_prescription(
    prescription: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor]))
):
    from app.models.patient import Patient
    
    # Resolve Patient
    patient_id = prescription.patient_id
    if not patient_id:
        if prescription.mrn:
            p = db.query(Patient).filter(Patient.mrn == prescription.mrn).first()
            if p: patient_id = p.id
        if not patient_id and prescription.patient:
            name_parts = prescription.patient.split()
            if len(name_parts) >= 2:
                p = db.query(Patient).filter(Patient.first_name == name_parts[0], Patient.last_name == name_parts[-1]).first()
                if p: patient_id = p.id
    
    if not patient_id:
        # Fallback to patient 1 for demo purposes if not found
        patient_id = 1
        
    drug_name = prescription.drug_name or prescription.drug

    # ==========================================
    # Phase 3: AI Clinical Decision Support (CDS) Hook
    # ==========================================
    # In a real app, this would call the Gemini API. We simulate the AI detecting a drug interaction.
    # We check if drug is Lisinopril and patient has history of Angioedema, etc.
    from app.models.medical_history import MedicalHistory
    from app.models.allergy import Allergy
    
    patient_history = db.query(MedicalHistory).filter(MedicalHistory.patient_id == patient_id).all()
    patient_allergies = db.query(Allergy).filter(Allergy.patient_id == patient_id).all()
    
    history_str = ", ".join([h.condition for h in patient_history])
    allergy_str = ", ".join([a.substance for a in patient_allergies])
    
    ai_alert_triggered = False
    alert_title = ""
    alert_desc = ""
    
    # Mock AI logic for drug interactions
    if "Lisinopril" in drug_name and "Angioedema" in history_str:
        ai_alert_triggered = True
        alert_title = "DANGEROUS INTERACTION: Lisinopril & Angioedema"
        alert_desc = "AI CDS Alert: Patient has a history of Angioedema. ACE inhibitors like Lisinopril are contraindicated."
    elif "Penicillin" in drug_name and "Penicillin" in allergy_str:
        ai_alert_triggered = True
        alert_title = "SEVERE ALLERGY: Penicillin"
        alert_desc = "AI CDS Alert: Patient has a documented severe allergy to Penicillin."
        
    # If the AI triggered an alert, we generate a PlanDefinition resource.
    if ai_alert_triggered:
        from app.models.plan_definition import PlanDefinition
        pd = PlanDefinition(
            patient_id=patient_id,
            title=alert_title,
            description=alert_desc,
            status="active"
        )
        db.add(pd)
        db.commit()
        db.refresh(pd)
        
        from app.services.fhir_sync import sync_plan_definition
        # Send the CDS Alert to FHIR
        try:
            sync_plan_definition(pd.id, pd.patient_id, pd.title, pd.description, pd.status)
        except Exception as e:
            print(f"Failed to sync PlanDefinition: {e}")

    # ==========================================
    # 1. Save to Database
    # ==========================================
    db_rx = Prescription(
        patient_id=patient_id,
        prescriber_id=current_user.id,
        drug_name=drug_name,
        sig=prescription.sig,
        refills=prescription.refills
    )
    db.add(db_rx)
    db.commit()
    db.refresh(db_rx)

    # 2. Sync to HAPI FHIR Server as MedicationRequest
    fhir_payload = {
        "resourceType": "MedicationRequest",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {
            "text": drug_name
        },
        "subject": {
            "reference": f"Patient/patient-{patient_id}"
        },
        "requester": {
            "reference": f"Practitioner/user-{current_user.id}"
        },
        "dosageInstruction": [
            {
                "text": prescription.sig
            }
        ],
        "dispenseRequest": {
            "numberOfRepeatsAllowed": prescription.refills
        },
        "authoredOn": datetime.utcnow().isoformat() + "Z"
    }

    try:
        response = requests.post(f"{FHIR_URL}/MedicationRequest", json=fhir_payload, headers={"Content-Type": "application/fhir+json"})
        response.raise_for_status()
        fhir_data = response.json()
        
        # 3. Update DB with FHIR ID
        db_rx.fhir_id = fhir_data.get("id")
        db.commit()
        
    except Exception as e:
        # We don't fail the DB write if FHIR is down, just log it.
        print(f"Failed to sync prescription {db_rx.id} to FHIR: {e}")

    return {
        "id": db_rx.id,
        "patient": f"{db_rx.patient.first_name} {db_rx.patient.last_name}",
        "mrn": db_rx.patient.mrn,
        "drug": db_rx.drug_name,
        "sig": db_rx.sig,
        "prescriber": current_user.username,
        "date": db_rx.date_prescribed.strftime("%Y-%m-%d"),
        "refills": db_rx.refills,
        "status": db_rx.status.value,
        "fhir_id": db_rx.fhir_id,
        "ai_cds_alert": alert_title if ai_alert_triggered else None
    }
