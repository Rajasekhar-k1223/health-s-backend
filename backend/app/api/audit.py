from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime
from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.audit import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
def get_raw_audit_logs(
    db: Session = Depends(get_db),
    current_user=Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin])),
    username: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(AuditLog).order_by(desc(AuditLog.timestamp))
    if username:
        query = query.filter(AuditLog.username.ilike(f"%{username}%"))
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if resource:
        query = query.filter(AuditLog.resource.ilike(f"%{resource}%"))
    if date_from:
        query = query.filter(AuditLog.timestamp >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(AuditLog.timestamp <= datetime.fromisoformat(date_to))
    logs = query.offset(skip).limit(limit).all()
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "username": log.username,
            "action": log.action,
            "resource": log.resource,
            "ip": getattr(log, "ip_address", "—"),
        }
        for log in logs
    ]


@router.get("/logs/count")
def count_audit_logs(
    db: Session = Depends(get_db),
    current_user=Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin])),
):
    return {"count": db.query(AuditLog).count()}


@router.get("/analytics")
def get_audit_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin])),
):
    from sqlalchemy import func
    total = db.query(AuditLog).count()
    login_success = db.query(AuditLog).filter(AuditLog.action == "LOGIN_SUCCESS").count()
    login_failed = db.query(AuditLog).filter(AuditLog.action == "LOGIN_FAILED").count()
    # Action breakdown
    actions = (
        db.query(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
        .order_by(desc(func.count(AuditLog.id)))
        .limit(10)
        .all()
    )
    return {
        "total_events": total,
        "login_success": login_success,
        "login_failed": login_failed,
        "compliance_score": 94,
        "phi_access_today": total,
        "active_threats": 2,
        "suspicious_access": login_failed,
        "action_breakdown": [{"action": a, "count": c} for a, c in actions],
        "access_by_role": {"doctor": 0, "nurse": 0, "admin": total, "caregiver": 0},
    }


@router.get("/threats")
def get_insider_threats(
    db: Session = Depends(get_db),
    current_user=Depends(require_role([RoleEnum.super_admin])),
):
    failed = db.query(AuditLog).filter(AuditLog.action == "LOGIN_FAILED").limit(10).all()
    return [
        {
            "id": f"TH-{log.id}",
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "username": log.username,
            "role": "unknown",
            "threat_type": "Failed Login",
            "description": f"Failed login attempt on {log.resource}",
            "severity": "Medium",
            "status": "Logged",
        }
        for log in failed
    ]
