from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.websocket import manager

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.websocket("/ws/{patient_id}")
async def websocket_endpoint(websocket: WebSocket, patient_id: int):
    """
    WebSocket endpoint for live telemetry monitoring.
    Clients connect to this endpoint to receive continuous high-frequency streams for a specific patient.
    Use patient_id=0 to subscribe to the global central dashboard feed.
    """
    await manager.connect(websocket, patient_id)
    try:
        while True:
            # We don't expect data from the client, but we must keep the connection alive
            data = await websocket.receive_text()
            # If the client sends a heartbeat/ping, we can optionally respond
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, patient_id)
