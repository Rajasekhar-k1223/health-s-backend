import asyncio
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.patient import Patient
from app.models.alert import Alert
from app.models.telehealth import TelehealthSession
from app.schemas.copilot import CopilotQuery, CopilotResponse

router = APIRouter(prefix="/copilot", tags=["copilot"])

async def generate_ollama_inference(prompt: str) -> str:
    """Calls a local Ollama LLM to answer the Copilot query."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False
                }
            )
            if response.status_code == 200:
                return response.json().get("response", "Error generating response.")
            else:
                return f"LLM Error: Status {response.status_code}"
    except httpx.RequestError as e:
        print(f"Failed to connect to Ollama: {e}")
        return f"(LLM Offline) Simulated Response for prompt: {prompt[:50]}..."

@router.post("/query", response_model=CopilotResponse)
async def copilot_query(
    query_in: CopilotQuery,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    prompt = ""
    sources = []
    
    # Context Aggregation
    if query_in.intent == "patient_summary" and query_in.patient_id:
        patient = db.query(Patient).filter(Patient.id == query_in.patient_id).first()
        if not patient: raise HTTPException(404, "Patient not found")
        prompt = f"Write a Patient Summary for: {patient.first_name} {patient.last_name}, Age: {patient.age}."
        sources.append(f"Patient/{patient.id}")
        
    elif query_in.intent == "alert_explain" and query_in.context_id:
        alert = db.query(Alert).filter(Alert.id == query_in.context_id).first()
        if not alert: raise HTTPException(404, "Alert not found")
        prompt = f"Provide an Alert Explanation for: {alert.alert_type} - {alert.metric} = {alert.value}. Risk Score: {alert.severity_score}."
        sources.append(f"Alert/{alert.id}")
        
    elif query_in.intent == "risk_explain" and query_in.context_id:
        alert = db.query(Alert).filter(Alert.id == query_in.context_id).first()
        prompt = f"Provide a Risk Explanation for the score of {alert.severity_score if alert else 'unknown'}."
        
    elif query_in.intent == "visit_summary" and query_in.context_id:
        session = db.query(TelehealthSession).filter(TelehealthSession.id == query_in.context_id).first()
        prompt = f"Write a patient-friendly Visit Summary based on the transcript: {session.transcription if session else 'No transcript'}"
        sources.append(f"TelehealthSession/{query_in.context_id}")
        
    elif query_in.intent == "draft_care_plan":
        prompt = "Draft a Care Plan based on recent FHIR encounters and telemetry."
        
    elif query_in.intent == "draft_note":
        prompt = "Draft a general Clinical Note for the patient."
        
    else:
        prompt = query_in.query or "General Chat"

    # Inference
    response_text = await generate_ollama_inference(prompt)
    
    # Strict Compliance Disclaimer
    disclaimer = "\n\nClinical insights for review. This is not a diagnosis. Clinical review is recommended."
    final_response = response_text + disclaimer
    
    return CopilotResponse(response=final_response, sources=sources)
