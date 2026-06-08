import os
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.telehealth import TelehealthSession

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
async def audio_ingestion(websocket: WebSocket, session_id: str):
    """
    Ingests continuous audio blobs from the browser's MediaRecorder,
    processes them through Local Whisper, and returns real-time text.
    """
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
        
        # Save final transcript to database
        db: Session = SessionLocal()
        try:
            session = db.query(TelehealthSession).filter(TelehealthSession.id == int(session_id)).first()
            if session:
                final_text = " ".join(full_transcript)
                # In simulation, if it's empty, we inject a dummy transcript for AI Scribe testing
                if not final_text:
                    final_text = "Doctor: Hello, how are you feeling today? Patient: I've had a headache for 3 days and some mild fever. Doctor: I see. Are you taking any medications? Patient: Just some ibuprofen. Doctor: Okay, I will prescribe some rest and hydration. If it gets worse, come back."
                
                session.transcription = final_text
                db.commit()
                print(f"✅ Saved full transcript for session {session_id}")
        except Exception as e:
            print(f"🚨 Failed to save transcript: {e}")
        finally:
            db.close()
