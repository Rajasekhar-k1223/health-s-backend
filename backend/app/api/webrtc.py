from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from typing import Dict, List
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.core.security import SECRET_KEY, ALGORITHM
from app.core.database import get_db
from app.models.user import User, RoleEnum
from app.models.telehealth import TelehealthSession
from app.models.patient import Patient
import json

router = APIRouter(prefix="/webrtc", tags=["webrtc"])

# In-memory room manager for WebRTC signaling
class ConnectionManager:
    def __init__(self):
        # Maps room_id -> list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        print(f"🔗 WebRTC Client joined room {room_id}. Total: {len(self.active_connections[room_id])}")

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if len(self.active_connections[room_id]) == 0:
                del self.active_connections[room_id]
        print(f"❌ WebRTC Client left room {room_id}.")

    async def broadcast(self, message: str, room_id: str, sender: WebSocket):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                if connection != sender:
                    try:
                        await connection.send_text(message)
                    except Exception as e:
                        print(f"WebRTC Broadcast Error: {e}")

manager = ConnectionManager()

@router.websocket("/ws/{room_id}")
async def webrtc_signaling(
    websocket: WebSocket, 
    room_id: str,
    token: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for WebRTC signaling (SDP offers/answers, ICE candidates).
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
        session_model = db.query(TelehealthSession).filter(TelehealthSession.id == int(room_id)).first()
        if session_model:
            patient = db.query(Patient).filter(Patient.id == session_model.patient_id).first()
            if not patient or patient.organization_id != user.organization_id:
                await websocket.close(code=1008, reason="Unauthorized: Video Room belongs to outside organization")
                return

    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast the signaling data to other peers in the room
            await manager.broadcast(data, room_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
