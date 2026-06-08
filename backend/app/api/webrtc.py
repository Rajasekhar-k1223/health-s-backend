from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
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
async def webrtc_signaling(websocket: WebSocket, room_id: str):
    """
    Handles WebRTC Signaling (SDP Offers, Answers, and ICE Candidates)
    for peer-to-peer video/audio connections.
    """
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast the signaling data to other peers in the room
            await manager.broadcast(data, room_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
