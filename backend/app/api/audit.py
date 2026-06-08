from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
import time

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/analytics")
def get_audit_analytics(
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.admin]))
):
    # Mocking advanced enterprise security analytics
    return {
        "phi_access_today": 1245,
        "active_threats": 2,
        "suspicious_access": 8,
        "compliance_score": 94,
        "access_by_role": {
            "doctor": 650,
            "nurse": 420,
            "admin": 150,
            "caregiver": 25
        }
    }

@router.get("/threats")
def get_insider_threats(
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.admin]))
):
    # Mocking detected insider threats (bulk scraping, off-hours)
    return [
        {
            "id": "TH-9021",
            "timestamp": "2023-10-26T03:15:00Z",
            "username": "nurse_j_smith",
            "role": "nurse",
            "threat_type": "Off-Hours Access",
            "description": "Accessed PT-1002 record at 3:15 AM outside of scheduled shift.",
            "severity": "Medium",
            "status": "Investigating"
        },
        {
            "id": "TH-9022",
            "timestamp": "2023-10-26T14:45:12Z",
            "username": "dr_m_rogers",
            "role": "doctor",
            "threat_type": "Bulk Velocity Download",
            "description": "Accessed 45 distinct patient records within a 2-minute window. Flagged as potential data scraping.",
            "severity": "High",
            "status": "Active"
        }
    ]

@router.get("/logs")
def get_raw_audit_logs(
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.admin]))
):
    # Mocking a live stream of raw audit logs
    return [
        {"id": 1005, "timestamp": "2023-10-26T15:30:10Z", "username": "dr_s_jenkins", "action": "PHI_READ", "resource": "/patients/1001", "ip": "10.0.1.45"},
        {"id": 1004, "timestamp": "2023-10-26T15:28:44Z", "username": "admin_system", "action": "DEVICE_ASSIGN", "resource": "/devices/SN-003", "ip": "10.0.1.2"},
        {"id": 1003, "timestamp": "2023-10-26T15:25:00Z", "username": "nurse_j_smith", "action": "PHI_READ", "resource": "/patients/1005", "ip": "10.0.1.78"},
        {"id": 1002, "timestamp": "2023-10-26T14:45:12Z", "username": "dr_m_rogers", "action": "PHI_EXPORT", "resource": "/patients/*", "ip": "10.0.1.12"},
        {"id": 1001, "timestamp": "2023-10-26T10:00:00Z", "username": "dr_s_jenkins", "action": "LOGIN_SUCCESS", "resource": "/auth/token", "ip": "10.0.1.45"}
    ]
