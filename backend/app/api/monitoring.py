from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.core.websocket import manager
from app.core.security import SECRET_KEY, ALGORITHM
from app.core.database import get_db
from app.models.user import User, RoleEnum
from app.models.patient import Patient

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.websocket("/ws/{patient_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    patient_id: int,
    token: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for live telemetry monitoring.
    Clients connect to this endpoint to receive continuous high-frequency streams for a specific patient.
    Use patient_id=0 to subscribe to the global central dashboard feed.
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
    if user.role != RoleEnum.super_admin and patient_id != 0:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient or patient.organization_id != user.organization_id:
            await websocket.close(code=1008, reason="Unauthorized: Patient does not belong to your organization")
            return
            
    # If subscribing to global feed (patient_id=0), block non-super-admins to prevent global data leakage
    if patient_id == 0 and user.role != RoleEnum.super_admin:
        await websocket.close(code=1008, reason="Unauthorized: Global feed requires super_admin")
        return

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
