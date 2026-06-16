from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import requests
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.claim import Claim
from app.models.encounter import Encounter

router = APIRouter(prefix="/billing", tags=["billing"])

FHIR_URL = "http://localhost:8080/fhir"

@router.get("/claims", response_model=List[Dict[str, Any]])
def get_billing_claims(
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    claims = db.query(Claim).order_by(Claim.date_created.desc()).all()
    result = []
    for c in claims:
        result.append({
            "id": c.claim_number,
            "patient": f"{c.patient.first_name} {c.patient.last_name}" if c.patient else "Unknown",
            "amount": f"${c.amount:,.2f}",
            "status": c.status.value,
            "date": c.date_created.strftime("%Y-%m-%d"),
            "payer": c.payer or "Self-Pay"
        })
    return result

@router.post("/generate-claim/{encounter_id}", response_model=Dict[str, Any])
def generate_claim_for_encounter(
    encounter_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor]))
):
    encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
    if not encounter:
        # For demo purposes, we will bypass strict encounter checking if it's 999 
        # (the mock ID sent by the frontend utility button)
        if encounter_id == 999:
            from app.models.patient import Patient
            patient = db.query(Patient).first()
            if not patient: raise HTTPException(status_code=404, detail="No patients found to mock claim")
            
            # Create a mock encounter
            encounter = Encounter(patient_id=patient.id, doctor_id=current_user.id, reason="Demo Consultation")
            db.add(encounter)
            db.commit()
            db.refresh(encounter)
        else:
            raise HTTPException(status_code=404, detail="Encounter not found")
    
    # ==========================================
    # Phase 3: AI Automated Medical Billing (Auto-Coding)
    # ==========================================
    # We simulate the AI reading the doctor's note or insight and suggesting ICD-10/CPT codes.
    from app.models.insight import Insight
    from app.models.medical_history import MedicalHistory
    
    # Try to find the latest insight or history to base the billing on
    latest_insight = db.query(Insight).filter(Insight.patient_id == encounter.patient_id).order_by(Insight.timestamp.desc()).first()
    latest_history = db.query(MedicalHistory).filter(MedicalHistory.patient_id == encounter.patient_id).order_by(MedicalHistory.id.desc()).first()
    
    clinical_text = ""
    if latest_insight: clinical_text += latest_insight.summary
    if latest_history: clinical_text += " " + latest_history.condition
    
    icd10_code = "Z00.00" # Default general exam
    icd10_display = "Encounter for general adult medical examination"
    cpt_code = "99213" # Default level 3 visit
    cpt_display = "Office or other outpatient visit"
    amount = 250.00
    
    # Mock AI Extraction Logic
    if "Pneumonia" in clinical_text or "pneumonia" in clinical_text:
        icd10_code = "J18.9"
        icd10_display = "Pneumonia, unspecified organism"
        cpt_code = "99214" # Level 4 visit
        amount = 350.00
    elif "Diabetes" in clinical_text or "diabetes" in clinical_text:
        icd10_code = "E11.9"
        icd10_display = "Type 2 diabetes mellitus without complications"
        cpt_code = "99214"
        amount = 300.00
    elif "Hypertension" in clinical_text or "hypertension" in clinical_text:
        icd10_code = "I10"
        icd10_display = "Essential (primary) hypertension"
        amount = 275.00
    
    # 1. Generate Claim in DB
    claim_num = f"CLM-{uuid.uuid4().hex[:6].upper()}"
    db_claim = Claim(
        claim_number=claim_num,
        patient_id=encounter.patient_id,
        encounter_id=encounter.id,
        organization_id=encounter.location_id,
        amount=amount,
        status="Pending",
        payer="Medicare"
    )
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    
    # 2. Sync to HAPI FHIR Server as Claim resource (With AI injected codes)
    fhir_payload = {
        "resourceType": "Claim",
        "status": "active",
        "type": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "institutional"}]
        },
        "use": "claim",
        "patient": {"reference": f"Patient/patient-{encounter.patient_id}"},
        "created": datetime.utcnow().isoformat() + "Z",
        "provider": {"reference": f"Practitioner/user-{current_user.id}"},
        "priority": {"coding": [{"code": "normal"}]},
        "diagnosis": [
            {
                "sequence": 1,
                "diagnosisCodeableConcept": {
                    "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": icd10_code, "display": icd10_display}]
                }
            }
        ],
        "item": [
            {
                "sequence": 1,
                "productOrService": {
                    "coding": [{"system": "http://www.ama-assn.org/go/cpt", "code": cpt_code, "display": cpt_display}]
                },
                "net": {
                    "value": amount,
                    "currency": "USD"
                }
            }
        ],
        "total": {
            "value": amount,
            "currency": "USD"
        }
    }
    
    try:
        res = requests.post(f"{FHIR_URL}/Claim", json=fhir_payload, headers={"Content-Type": "application/fhir+json"})
        if res.ok:
            db_claim.fhir_id = res.json().get("id")
            db.commit()
    except Exception as e:
        print(f"Failed to sync Claim {claim_num} to FHIR: {e}")
        
    return {
        "id": db_claim.claim_number,
        "patient": f"{db_claim.patient.first_name} {db_claim.patient.last_name}" if db_claim.patient else "Unknown",
        "amount": f"${db_claim.amount:,.2f}",
        "status": db_claim.status.value,
        "date": db_claim.date_created.strftime("%Y-%m-%d"),
        "payer": db_claim.payer,
        "fhir_id": db_claim.fhir_id
    }

@router.post("/simulate-adjudication", response_model=Dict[str, Any])
def simulate_adjudication(
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor]))
):
    from app.models.claim_response import ClaimResponse
    import random
    
    pending_claims = db.query(Claim).filter(Claim.status == "Pending").all()
    if not pending_claims:
        return {"status": "ok", "message": "No pending claims to adjudicate", "processed_count": 0}
        
    processed_count = 0
    for claim in pending_claims:
        # Simulate insurance logic: 80% paid, 20% denied
        is_paid = random.random() < 0.8
        
        claim.status = "Paid" if is_paid else "Denied"
        paid_amount = float(claim.amount) if is_paid else 0.0
        denial_reason = None if is_paid else "Missing prior authorization"
        
        cr = ClaimResponse(
            claim_id=claim.id,
            patient_id=claim.patient_id,
            outcome="complete" if is_paid else "error",
            disposition="Claim approved and paid" if is_paid else denial_reason,
            paid_amount=paid_amount,
            denied_reason=denial_reason
        )
        db.add(cr)
        
        # Sync ClaimResponse to FHIR
        fhir_cr = {
            "resourceType": "ClaimResponse",
            "status": "active",
            "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "institutional"}]},
            "use": "claim",
            "patient": {"reference": f"Patient/patient-{claim.patient_id}"},
            "created": datetime.utcnow().isoformat() + "Z",
            "insurer": {"display": claim.payer or "Unknown Payer"},
            "request": {"reference": f"Claim/{claim.fhir_id}" if claim.fhir_id else f"Claim/claim-{claim.id}"},
            "outcome": cr.outcome,
            "disposition": cr.disposition,
            "payment": {"amount": {"value": paid_amount, "currency": "USD"}}
        }
        
        try:
            res = requests.post(f"{FHIR_URL}/ClaimResponse", json=fhir_cr, headers={"Content-Type": "application/fhir+json"})
            if res.ok:
                cr.fhir_id = res.json().get("id")
        except Exception:
            pass
            
        import threading
        from app.services.fhir_sync import sync_explanation_of_benefit
        threading.Thread(target=sync_explanation_of_benefit, args=(cr.id, claim.id, claim.patient_id, current_user.id, cr.outcome, float(claim.amount), paid_amount)).start()
            
        processed_count += 1
        
    db.commit()
    return {"status": "ok", "message": f"Processed {processed_count} claims", "processed_count": processed_count}

from pydantic import BaseModel
class CoverageCreate(BaseModel):
    patient_id: int
    payor: str
    subscriber_id: str
    status: str = "active"

@router.post("/coverage")
def create_coverage(
    coverage: CoverageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.nurse]))
):
    from app.models.coverage import Coverage
    
    db_cov = Coverage(
        patient_id=coverage.patient_id,
        status=coverage.status,
        subscriber_id=coverage.subscriber_id,
        relationship="self",
        payor_id=1, # Mock payor ID
        plan_name="Standard Plan",
        network="In-Network"
    )
    db.add(db_cov)
    db.commit()
    db.refresh(db_cov)
    
    import threading
    from app.services.fhir_sync import sync_coverage
    threading.Thread(target=sync_coverage, args=(db_cov.id, db_cov.patient_id, db_cov.status, coverage.payor, db_cov.subscriber_id)).start()
    
    return db_cov
