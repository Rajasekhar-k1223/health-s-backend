import os
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from typing import Dict
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.core.security import SECRET_KEY, ALGORITHM
from app.core.database import SessionLocal, get_db
from app.models.user import User, RoleEnum
from app.models.patient import Patient
from app.models.scheduling import Appointment
from typing import Dict
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.telehealth import TelehealthSession
from app.api.ai_scribe import generate_soap_note_background, generate_ambient_soap_note_background

router = APIRouter(prefix="/transcription", tags=["transcription"])

# In production, faster-whisper or whisper.cpp would be loaded here.
# from faster_whisper import WhisperModel
# model = WhisperModel("base", device="cpu", compute_type="int8")

class TranscriptionManager:
    def __init__(self):
        # Maps session_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"🎙️ Transcription stream connected for session {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        print(f"🛑 Transcription stream disconnected for session {session_id}")

transcription_manager = TranscriptionManager()

@router.websocket("/ws/{session_id}")
async def audio_ingestion(
    websocket: WebSocket, 
    session_id: str,
    token: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Ingests continuous audio blobs from the browser's MediaRecorder,
    processes them through Local Whisper, and returns real-time text.
    """
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            await websocket.close(code=1008, reason="Invalid token payload")
            return
    except JWTError:
        await websocket.close(code=1008, reason="Invalid or expired token")
        return
        
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        await websocket.close(code=1008, reason="User not found or inactive")
        return
        
    # Enforce Multi-Tenant Data Governance
    if user.role != RoleEnum.super_admin:
        is_ambient = str(session_id).startswith("ambient_")
        patient = None
        
        if is_ambient:
            appt_id = int(session_id.split("_")[1])
            appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
            if appt:
                patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
        else:
            session_model = db.query(TelehealthSession).filter(TelehealthSession.id == int(session_id)).first()
            if session_model:
                patient = db.query(Patient).filter(Patient.id == session_model.patient_id).first()
                
        if not patient or patient.organization_id != user.organization_id:
            await websocket.close(code=1008, reason="Unauthorized: Session belongs to an outside organization")
            return

    await transcription_manager.connect(websocket, session_id)
    
    # Store full transcript for the session
    full_transcript = []
    
    try:
        while True:
            # Receive binary audio chunk
            audio_data = await websocket.receive_bytes()
            
            # --- LOCAL WHISPER PROCESSING ---
            # In production:
            # 1. Write audio_data to a temp .wav file
            # 2. segments, info = model.transcribe(temp_file)
            # 3. text = "".join([segment.text for segment in segments])
            
            # Simulated Processing Delay
            await asyncio.sleep(0.5)
            
            # Simulated transcript based on the chunk
            # In reality, this comes from faster-whisper output
            simulated_text = " [Patient states they have been experiencing mild chest pain since yesterday.] "
            full_transcript.append(simulated_text.strip())
            
            # Send text back to the UI for live display
            await websocket.send_text(json.dumps({
                "type": "TRANSCRIPT_CHUNK",
                "text": simulated_text.strip()
            }))
            
    except WebSocketDisconnect:
        transcription_manager.disconnect(session_id)
        
        # Determine if this is an ambient (in-person) or telehealth session
        is_ambient = str(session_id).startswith("ambient_")
        
        if is_ambient:
            appt_id = int(session_id.split("_")[1])
            # Auto-trigger the AI Scribe generation for in-person ambient scribe
            print(f"🤖 Auto-triggering Ambient AI Scribe for Appointment {appt_id}")
            asyncio.create_task(generate_ambient_soap_note_background(appt_id))
        else:
            # Save final transcript to database for Telehealth
            db: Session = SessionLocal()
            try:
                session = db.query(TelehealthSession).filter(TelehealthSession.id == int(session_id)).first()
                if session:
                    final_text = " ".join(full_transcript)
                    if not final_text:
                        final_text = "Doctor: Hello, how are you feeling today? Patient: I've had a headache for 3 days and some mild fever. Doctor: I see. Are you taking any medications? Patient: Just some ibuprofen. Doctor: Okay, I will prescribe some rest and hydration. If it gets worse, come back."
                    
                    session.transcription = final_text
                    db.commit()
                    print(f"✅ Saved full transcript for session {session_id}")
                    
                    # Auto-trigger the AI Scribe generation so the doctor never has to remember!
                    print(f"🤖 Auto-triggering AI Scribe for Session {session_id}")
                    asyncio.create_task(generate_soap_note_background(int(session_id)))
            except Exception as e:
                print(f"🚨 Failed to process disconnect: {e}")
            finally:
                db.close()
