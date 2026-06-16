from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import require_role, get_password_hash
from app.models.user import User, RoleEnum

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    username: str
    password: str
    role: RoleEnum
    is_active: bool = True


class UserUpdate(BaseModel):
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: RoleEnum
    is_active: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


ROLE_PERMISSIONS = {
    RoleEnum.super_admin: [
        "Manage Users", "Billing", "System Config", "Read/Write All Records",
        "Audit Logs", "Security Center", "OTA Updates", "Developer Portal"
    ],
    RoleEnum.hospital_admin: [
        "Manage Users (Hospital)", "Read/Write Patient Records",
        "Scheduling", "Reports", "Compliance Dashboard"
    ],
    RoleEnum.doctor: [
        "Read/Write Patient Charts", "Sign Notes", "Create Orders",
        "View AI Insights", "Telehealth", "Prescriptions"
    ],
    RoleEnum.nurse: [
        "Read Patient Charts", "Write Notes", "Acknowledge Alerts",
        "Log Vitals", "Medication Adherence"
    ],
    RoleEnum.patient: [
        "Read Own Records", "View Appointments", "Patient Education", "Messaging"
    ],
    RoleEnum.device: [
        "Telemetry Ingest", "Device Auth", "OTA Updates"
    ],
}


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[RoleEnum] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.offset(skip).limit(limit).all()


from app.services.fhir_sync import sync_practitioner
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = User(
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        is_active=user_in.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    if user.role in [RoleEnum.doctor, RoleEnum.nurse]:
        background_tasks.add_task(sync_practitioner, user.id)
        
    return user


@router.get("/permissions/{role}")
def get_role_permissions(
    role: RoleEnum,
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    return {
        "role": role,
        "permissions": ROLE_PERMISSIONS.get(role, [])
    }


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user.is_active = False
    db.commit()
    return {"message": f"User {user.username} deactivated"}


@router.get("/stats/summary")
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    total = db.query(User).count()
    active = db.query(User).filter(User.is_active == True).count()
    by_role = {}
    for role in RoleEnum:
        by_role[role.value] = db.query(User).filter(User.role == role).count()
    return {"total": total, "active": active, "inactive": total - active, "by_role": by_role}
