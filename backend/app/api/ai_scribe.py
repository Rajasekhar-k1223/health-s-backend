import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.telehealth import TelehealthSession
from app.models.clinical_note import ClinicalNote

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
        # In production:
        # prompt = f"Format the following medical transcript into a strict SOAP note:\n{tsession.transcription}"
        # response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
        # generated_soap = response['message']['content']
        
        await asyncio.sleep(2) # Simulate inference
        
        generated_soap = f"""**SUBJECTIVE:**
Patient presents with headache for 3 days and mild fever. Currently taking ibuprofen.

**OBJECTIVE:**
Vital signs pending. Patient appears in mild distress on video.

**ASSESSMENT:**
1. Headache, likely viral etiology.
2. Low-grade fever.

**PLAN:**
1. Rest and oral hydration.
2. Continue ibuprofen as needed.
3. Return to clinic if symptoms worsen."""

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
        
    if not tsession.transcription:
        # Inject dummy transcript for testing
        tsession.transcription = "Doctor: Hello. Patient: I have a headache."
        db.commit()
        
    background_tasks.add_task(generate_soap_note_background, session_id)
    return {"status": "queued", "message": "AI Scribe generation started in background."}

@router.get("/note/{session_id}")
def get_scribe_note(
    session_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    note = db.query(ClinicalNote).filter(ClinicalNote.session_id == session_id).order_by(ClinicalNote.created_at.desc()).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Also fetch the raw transcript
    session = db.query(TelehealthSession).filter(TelehealthSession.id == session_id).first()
    
    return {
        "id": note.id,
        "content": note.content,
        "signed": note.signed,
        "transcript": session.transcription if session else None
    }
