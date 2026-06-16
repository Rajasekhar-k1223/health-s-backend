from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import secrets
import hashlib

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.device import Device
from app.models.device_auth import DeviceCredential
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceAssign, DeviceCredentialResponse

router = APIRouter(prefix="/devices", tags=["devices"])

from app.services.fhir_sync import sync_device_to_fhir
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

@router.post("/", response_model=DeviceResponse)
def register_device(
    device_in: DeviceCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    existing = db.query(Device).filter(Device.device_id == device_in.device_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device ID already registered")
        
    new_device = Device(**device_in.dict())
    
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin:
        new_device.organization_id = current_user.organization_id
        
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    
    background_tasks.add_task(sync_device_to_fhir, new_device)
    return new_device

@router.get("/", response_model=List[DeviceResponse])
def get_devices(
    skip: int = 0, limit: int = 100, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    query = db.query(Device)
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin:
        query = query.filter(Device.organization_id == current_user.organization_id)
        
    return query.offset(skip).limit(limit).all()

@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin and device.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Device does not belong to your organization")
        
    for key, value in device_update.dict(exclude_unset=True).items():
        setattr(device, key, value)
        
    db.commit()
    db.refresh(device)
    return device

@router.put("/{device_id}/assign", response_model=DeviceResponse)
def assign_device(
    device_id: int,
    assignment: DeviceAssign,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin and device.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Device does not belong to your organization")
        
    device.patient_id = assignment.patient_id
    db.commit()
    db.refresh(device)
    return device

@router.post("/{device_id}/credentials")
def generate_device_credentials(
    device_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin and device.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Device does not belong to your organization")
        
    # Generate an API key (only returned once)
    api_key = secrets.token_urlsafe(32)
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Invalidate old keys
    db.query(DeviceCredential).filter(DeviceCredential.device_id == device_id).update({"is_active": False})
    
    cred = DeviceCredential(device_id=device_id, api_key_hash=api_key_hash, is_active=True)
    db.add(cred)
    db.commit()
    
    return {
        "device_id": device_id,
        "api_key": api_key,
        "message": "Store this key safely. It will not be displayed again."
    }
