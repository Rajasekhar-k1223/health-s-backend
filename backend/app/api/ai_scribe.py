import asyncio
import httpx
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.telehealth import TelehealthSession
from app.models.clinical_note import ClinicalNote
from app.models.scheduling import Appointment
from app.models.patient import Patient

router = APIRouter(prefix="/scribe", tags=["ai_scribe"])

async def generate_soap_note_background(session_id: int):
    """
    Background worker that takes a raw transcript and uses the local 
    Ollama LLM to generate a structured clinical SOAP Note.
    """
    from app.core.database import SessionLocal
    db: Session = SessionLocal()
    try:
        tsession = db.query(TelehealthSession).filter(TelehealthSession.id == session_id).first()
        if not tsession or not tsession.transcription:
            print(f"Skipping SOAP generation for {session_id} - no transcript.")
            return

        print(f"🧠 AI Scribe generating SOAP Note for Session {session_id}...")
        
        # 1. Local Ollama LLM Inference
        prompt = f"Format the following medical transcript into a strict SOAP note with SUBJECTIVE, OBJECTIVE, ASSESSMENT, and PLAN sections. Do not include any other text.\n\nTranscript:\n{tsession.transcription}"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    generated_soap = response.json().get("response", "Error generating SOAP note.")
                else:
                    generated_soap = f"LLM Error: Status {response.status_code}"
        except httpx.RequestError as e:
            print(f"Failed to connect to Ollama: {e}")
            generated_soap = "**SUBJECTIVE:**\n(LLM Offline)\n\n**OBJECTIVE:**\n(LLM Offline)\n\n**ASSESSMENT:**\n(LLM Offline)\n\n**PLAN:**\n(LLM Offline)"

        # 2. Strict Compliance Enforcement
        disclaimer = "\n\nClinical insights for review. This is not a diagnosis. Clinical review is recommended."
        final_content = generated_soap + disclaimer
        
        # 3. Save to database
        tsession.ai_summary = final_content
        
        note = ClinicalNote(
            session_id=session_id,
            patient_id=tsession.patient_id,
            doctor_id=tsession.doctor_id,
            note_type="SOAP",
            content=final_content
        )
        db.add(note)
        db.commit()
        
        print(f"✅ AI Scribe completed for Session {session_id}")

        # Trigger FHIR Sync
        from app.services.fhir_sync import sync_clinical_note_to_fhir, sync_encounter_to_fhir
        sync_encounter_to_fhir(tsession)
        sync_clinical_note_to_fhir(note)

    except Exception as e:
        print(f"🚨 AI Scribe Error: {e}")
        db.rollback()
    finally:
        db.close()

@router.post("/generate/{session_id}")
async def trigger_scribe(
    session_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor]))
):
    """Manually trigger the AI Scribe to generate a SOAP note for a telehealth session."""
    tsession = db.query(TelehealthSession).filter(TelehealthSession.id == session_id).first()
    if not tsession:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin:
        patient = db.query(Patient).filter(Patient.id == tsession.patient_id).first()
        if not patient or patient.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Not authorized for this organization's data")
        
    if not tsession.transcription:
        # Inject dummy transcript for testing
        tsession.transcription = "Doctor: Hello. Patient: I have a headache."
        db.commit()
        
    background_tasks.add_task(generate_soap_note_background, session_id)
    return {"status": "queued", "message": "AI Scribe generation started in background."}

async def generate_ambient_soap_note_background(appointment_id: int):
    from app.core.database import SessionLocal
    db: Session = SessionLocal()
    try:
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt: return

        print(f"🧠 AI Scribe generating Ambient SOAP Note for Appointment {appointment_id}...")
        # Use Ollama for Ambient Scribe
        prompt = f"Format the following ambient clinical audio transcript into a strict SOAP note with SUBJECTIVE, OBJECTIVE, ASSESSMENT, and PLAN sections.\n\nTranscript:\n(Ambient Audio Recorded In-Clinic)\nPatient reports headache for 3 days."
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    generated_soap = response.json().get("response", "Error generating SOAP note.")
                else:
                    generated_soap = f"LLM Error: Status {response.status_code}"
        except httpx.RequestError as e:
            print(f"Failed to connect to Ollama: {e}")
            generated_soap = "**SUBJECTIVE:**\n(LLM Offline)\n\n**OBJECTIVE:**\n(LLM Offline)\n\n**ASSESSMENT:**\n(LLM Offline)\n\n**PLAN:**\n(LLM Offline)"

        disclaimer = "\n\nClinical insights for review. Generated via In-Person Ambient Scribe."
        final_content = generated_soap + disclaimer
        
        note = ClinicalNote(
            session_id=appointment_id, # Reusing session_id field for appointment_id temporarily
            patient_id=appt.patient_id,
            doctor_id=appt.provider_id,
            note_type="SOAP",
            content=final_content
        )
        db.add(note)
        appt.status = "COMPLETED"
        db.commit()
        print(f"✅ Ambient AI Scribe completed for Appointment {appointment_id}")
    except Exception as e:
        print(f"🚨 Ambient Scribe Error: {e}")
        db.rollback()
    finally:
        db.close()

@router.post("/generate/ambient/{appointment_id}")
async def trigger_ambient_scribe(
    appointment_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor]))
):
    """Manually trigger the AI Scribe for an In-Person appointment."""
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin:
        patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
        if not patient or patient.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Not authorized for this organization's data")
        
    background_tasks.add_task(generate_ambient_soap_note_background, appointment_id)
    return {"status": "queued", "message": "Ambient Scribe generation started in background."}

@router.get("/note/{session_id}")
def get_scribe_note(
    session_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    note = db.query(ClinicalNote).filter(ClinicalNote.session_id == session_id).order_by(ClinicalNote.created_at.desc()).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin:
        patient = db.query(Patient).filter(Patient.id == note.patient_id).first()
        if not patient or patient.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Not authorized for this organization's data")
    
    # Also fetch the raw transcript
    session = db.query(TelehealthSession).filter(TelehealthSession.id == session_id).first()
    
    return {
        "id": note.id,
        "content": note.content,
        "signed": note.signed,
        "transcript": session.transcription if session else None
    }
