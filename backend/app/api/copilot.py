import asyncio
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

async def simulate_ollama_inference(prompt: str) -> str:
    """Simulates a call to a local Ollama LLM with various prompt behaviors."""
    await asyncio.sleep(1.5)
    
    if "Patient Summary" in prompt:
        return "The patient is a 65-year-old male with a history of hypertension. Recent telemetry indicates stable heart rate but occasional SpO2 dips during sleep. No recent acute events."
    elif "Alert Explanation" in prompt:
        return "The alert was triggered because the patient's SpO2 dropped below 90% for over 3 minutes. This may indicate sleep apnea or respiratory distress. Immediate assessment is advised."
    elif "Risk Explanation" in prompt:
        return "The AI Risk Score of 85 was calculated due to compounding factors: advanced age, history of hypertension, and a recent cluster of high-severity alerts related to tachycardia."
    elif "Visit Summary" in prompt:
        return "Patient reported a mild headache for 3 days and low-grade fever. Recommended rest, hydration, and over-the-counter ibuprofen. Return if symptoms worsen."
    elif "Care Plan" in prompt:
        return "GOAL: Maintain SpO2 > 92%.\nACTIVITY 1: Daily breathing exercises.\nACTIVITY 2: Continuous pulse oximetry monitoring during sleep."
    elif "Clinical Note" in prompt:
        return "Patient reviewed today. Vital signs are mostly stable. Continues on current medication regimen. Next follow-up in 4 weeks."
    else:
        return "I am the Sentinel HealthOS AI Copilot. How can I assist you with this patient's clinical data today?"

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
    response_text = await simulate_ollama_inference(prompt)
    
    # Strict Compliance Disclaimer
    disclaimer = "\n\nClinical insights for review. This is not a diagnosis. Clinical review is recommended."
    final_response = response_text + disclaimer
    
    return CopilotResponse(response=final_response, sources=sources)
