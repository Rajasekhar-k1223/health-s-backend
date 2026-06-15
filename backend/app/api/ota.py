from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.ota import FirmwareRelease, OTADeployment, OTAStatus
from app.models.device import Device
from app.schemas.ota import FirmwareReleaseCreate, FirmwareReleaseResponse, OTADeploymentCreate, OTADeploymentResponse, OTACheckResponse

router = APIRouter(prefix="/ota", tags=["ota"])

@router.post("/firmware", response_model=FirmwareReleaseResponse)
def create_firmware_release(
    firmware_in: FirmwareReleaseCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin]))
):
    fw = FirmwareRelease(**firmware_in.dict())
    db.add(fw)
    db.commit()
    db.refresh(fw)
    return fw

@router.post("/deploy", response_model=OTADeploymentResponse)
def schedule_ota_deployment(
    deployment_in: OTADeploymentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin]))
):
    fw = db.query(FirmwareRelease).filter(FirmwareRelease.version == deployment_in.target_firmware_version).first()
    if not fw:
        raise HTTPException(status_code=404, detail="Firmware version not found")
        
    device = db.query(Device).filter(Device.id == deployment_in.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    dep = OTADeployment(**deployment_in.dict())
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep

@router.get("/devices/{device_id}/check", response_model=OTACheckResponse)
def check_for_updates(
    device_id: int,
    db: Session = Depends(get_db)
):
    # In a real scenario, device would authenticate via JWT here
    dep = db.query(OTADeployment).filter(
        OTADeployment.device_id == device_id,
        OTADeployment.status == OTAStatus.pending
    ).first()
    
    if not dep:
        return {"update_available": False}
        
    return {
        "update_available": True,
        "version": dep.firmware.version,
        "artifact_url": dep.firmware.artifact_url,
        "deployment_id": dep.id
    }

@router.patch("/deployments/{deployment_id}/status")
def update_deployment_status(
    deployment_id: int,
    status: OTAStatus,
    db: Session = Depends(get_db)
):
    dep = db.query(OTADeployment).filter(OTADeployment.id == deployment_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Deployment not found")
        
    dep.status = status
    if status == OTAStatus.success:
        # Update device current firmware version
        dep.device.firmware_version = dep.target_firmware_version
        
    db.commit()
    return {"status": "success", "new_status": status}
