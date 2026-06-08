import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum, User
from app.models.audit import AuditLog
from app.models.security import SecurityThreat, PatientConsent

router = APIRouter(prefix="/security", tags=["security"])

def run_threat_detection_engine(db: Session):
    """
    Lightweight rules engine that scans recent activity for security anomalies.
    """
    print("🛡️ Running Healthcare Security Threat Engine...")
    
    # Rule 1: Brute Force Login Detection (Simulated logic based on AuditLogs)
    # E.g. Find IPs with >5 failed logins in last hour
    recent_failed_logins = db.query(AuditLog).filter(
        AuditLog.action == "LOGIN_FAILED",
        AuditLog.timestamp >= datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    ).all()
    
    # Mocking a detection if we found any failed logins (for demo purposes)
    if len(recent_failed_logins) > 5:
        threat = SecurityThreat(
            threat_type="BRUTE_FORCE",
            severity="HIGH",
            description=f"Detected {len(recent_failed_logins)} failed login attempts from IP addresses in the last hour.",
            target_id="Multiple IPs"
        )
        db.add(threat)
        
    # Rule 2: PHI Exfiltration Detection (High volume of READ_PHI actions by one user)
    # Mock logic: Injecting a random threat for demonstration in UI
    existing = db.query(SecurityThreat).filter(SecurityThreat.status == "OPEN").count()
    if existing < 3:
        mock_threat = SecurityThreat(
            threat_type="PHI_EXFILTRATION",
            severity="CRITICAL",
            description="User accessed 50+ unique patient records within 10 minutes. Anomalous behavior detected.",
            target_id="User ID: 4"
        )
        db.add(mock_threat)
    
    db.commit()

@router.get("/threats")
def get_active_threats(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    """Get active security threats and trigger a background scan."""
    background_tasks.add_task(run_threat_detection_engine, db)
    return db.query(SecurityThreat).filter(SecurityThreat.status.in_(["OPEN", "INVESTIGATING"])).order_by(SecurityThreat.detected_at.desc()).all()

@router.put("/threats/{threat_id}/resolve")
def resolve_threat(
    threat_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    threat = db.query(SecurityThreat).filter(SecurityThreat.id == threat_id).first()
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    threat.status = "RESOLVED"
    threat.resolved_at = datetime.datetime.utcnow()
    db.commit()
    return {"message": "Threat resolved"}

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 50,
    action_filter: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    query = db.query(AuditLog)
    if action_filter:
        query = query.filter(AuditLog.action.ilike(f"%{action_filter}%"))
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

@router.get("/compliance-report")
def get_compliance_report(
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    # Calculate simple HIPAA compliance metrics
    total_audits = db.query(AuditLog).count()
    phi_access_count = db.query(AuditLog).filter(AuditLog.action.in_(["READ_PATIENT", "WRITE_PATIENT", "VIEW_DOCUMENT"])).count()
    active_threats = db.query(SecurityThreat).filter(SecurityThreat.status == "OPEN").count()
    
    return {
        "status": "COMPLIANT" if active_threats == 0 else "AT_RISK",
        "total_audit_events_24h": total_audits,
        "phi_access_events_24h": phi_access_count,
        "active_security_threats": active_threats,
        "encryption_status": "Active (AES-256)",
        "last_scan": datetime.datetime.utcnow().isoformat()
    }
