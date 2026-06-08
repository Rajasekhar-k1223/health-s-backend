from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.device_auth import DeviceCredential
from app.models.device import Device

router = APIRouter(prefix="/device-auth", tags=["device_auth"])

class DeviceTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

# For MVP, assuming API Key is sent in X-Device-API-Key header, and serial number in X-Device-Serial
@router.post("/token", response_model=DeviceTokenResponse)
def get_device_token(
    x_device_serial: str = Header(...),
    x_device_api_key: str = Header(...),
    db: Session = Depends(get_db)
):
    # Lookup device by serial
    device = db.query(Device).filter(Device.serial_number == x_device_serial).first()
    if not device:
        raise HTTPException(status_code=401, detail="Invalid device serial")

    # Lookup credentials
    cred = db.query(DeviceCredential).filter(DeviceCredential.device_id == device.id).first()
    if not cred or not cred.is_active:
        raise HTTPException(status_code=401, detail="Device credentials invalid or revoked")
        
    # In a real app, hash x_device_api_key and compare. For MVP, we do exact match.
    if cred.api_key_hash != x_device_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Generate JWT
    expiration_minutes = 60
    expire = datetime.utcnow() + timedelta(minutes=expiration_minutes)
    to_encode = {"sub": device.device_id, "type": "device", "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": encoded_jwt,
        "token_type": "bearer",
        "expires_in": expiration_minutes * 60
    }
