from fastapi import WebSocket
from typing import Dict, List, Set
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        # Map of patient_id -> set of active WebSockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, patient_id: int):
        await websocket.accept()
        if patient_id not in self.active_connections:
            self.active_connections[patient_id] = set()
        self.active_connections[patient_id].add(websocket)
        
    def disconnect(self, websocket: WebSocket, patient_id: int):
        if patient_id in self.active_connections:
            self.active_connections[patient_id].discard(websocket)
            if not self.active_connections[patient_id]:
                del self.active_connections[patient_id]
                
    async def broadcast_to_patient(self, patient_id: int, message: dict):
        """Send telemetry data to all clients watching a specific patient"""
        if patient_id in self.active_connections:
            # We convert to JSON string once
            msg_str = json.dumps(message)
            disconnected = set()
            
            for connection in self.active_connections[patient_id]:
                try:
                    await connection.send_text(msg_str)
                except Exception:
                    disconnected.add(connection)
                    
            # Clean up dropped connections
            for conn in disconnected:
                self.disconnect(conn, patient_id)

    async def broadcast_to_all(self, message: dict):
        """Send data to all active monitoring stations (e.g. for the central dashboard)"""
        msg_str = json.dumps(message)
        disconnected = []
        
        for patient_id, connections in self.active_connections.items():
            for connection in list(connections):
                try:
                    await connection.send_text(msg_str)
                except Exception:
                    disconnected.append((connection, patient_id))
                    
        for conn, pid in disconnected:
            self.disconnect(conn, pid)

manager = ConnectionManager()
