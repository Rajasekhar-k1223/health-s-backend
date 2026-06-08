from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.alert import Alert
from app.core.websocket import manager
import asyncio
import json
import random

async def generate_ai_insight(alert_id: int):
    """
    Background task to generate an AI clinical insight for a given alert.
    Queries the local Ollama LLM to assess severity and append a strict disclaimer.
    """
    db: Session = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return
            
        # Simulated call to Ollama (local LLM)
        # In production:
        # prompt = f"Analyze patient alert: {alert.alert_type} - {alert.metric} = {alert.value}. Provide a short risk score and summary."
        # response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
        
        await asyncio.sleep(2) # Simulate LLM inference delay
        
        # Determine simulated score and insight based on alert type
        if alert.alert_type == "Cardiac":
            score = random.randint(70, 95)
            insight_text = f"Patient's {alert.metric} is {alert.value}, which indicates potential arrhythmia or tachycardia. Immediate review of continuous ECG is advised."
        elif alert.alert_type == "Respiratory":
            score = random.randint(60, 90)
            insight_text = f"Patient's {alert.metric} dropped to {alert.value}. Risk of hypoxia detected."
        elif alert.alert_type == "Fall":
            score = 99
            insight_text = "Sudden acceleration detected consistent with a fall. Assess patient immediately for trauma."
        elif alert.alert_type == "Device Failure":
            score = random.randint(40, 60)
            insight_text = "Telemetry stream interrupted. Verify device battery and connection."
        else:
            score = random.randint(30, 70)
            insight_text = f"Anomaly detected in {alert.metric} ({alert.value}). Monitor for trends."
            
        # CRITICAL RULE: AI outputs must always display the clinical disclaimer
        disclaimer = "\n\nClinical insights for review. This is not a diagnosis. Clinical review is recommended."
        
        alert.severity_score = score
        alert.ai_insight = insight_text + disclaimer
        
        db.commit()
        db.refresh(alert)
        
        # Broadcast the updated alert to the UI via WebSockets
        # If the patient has a dashboard open, update it
        if alert.patient_id:
            await manager.broadcast_to_patient(alert.patient_id, {
                "type": "ALERT_UPDATE",
                "alert": {
                    "id": alert.id,
                    "alert_type": alert.alert_type,
                    "severity_score": alert.severity_score,
                    "ai_insight": alert.ai_insight
                }
            })
            
        # Also broadcast to the global dashboard feed
        await manager.broadcast_to_patient(0, {
            "type": "GLOBAL_ALERT",
            "alert": {
                "id": alert.id,
                "patient_id": alert.patient_id,
                "alert_type": alert.alert_type,
                "severity_score": alert.severity_score,
                "ai_insight": alert.ai_insight
            }
        })
            
    except Exception as e:
        print(f"Error generating AI insight for alert {alert_id}: {e}")
        db.rollback()
    finally:
        db.close()
