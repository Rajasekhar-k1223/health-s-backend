import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.core.database import SessionLocal
from app.models.audit import AuditLog

client = TestClient(app)

def test_hipaa_audit_log_get_request():
    """
    Test that merely viewing a patient's chart (GET request)
    generates a legally compliant HIPAA audit log with the correct username.
    """
    db = SessionLocal()
    # Clear previous logs for clean test
    db.query(AuditLog).delete()
    db.commit()

    # Simulate doctor viewing a patient list
    token = create_access_token(data={"sub": "dr_smith_1", "role": "doctor", "organization_id": 1})
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/patients/", headers=headers)
    assert res.status_code == 200

    # Verify that the middleware intercepted the GET and wrote to the DB
    logs = db.query(AuditLog).all()
    assert len(logs) == 1
    
    log = logs[0]
    assert log.username == "dr_smith_1"
    assert log.action == "GET"
    assert "/patients" in log.resource
    
    db.close()
