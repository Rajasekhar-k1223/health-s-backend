import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import RoleEnum
from app.core.security import create_access_token

client = TestClient(app)

def test_tenant_isolation_patients():
    """
    Test that a doctor in Org A cannot access a patient in Org B.
    """
    # Create mock doctor token for Org 1
    token_doc_a = create_access_token(data={"sub": "dr_smith_1", "role": "doctor", "organization_id": 1})
    headers_a = {"Authorization": f"Bearer {token_doc_a}"}

    # Fetch patients for Org 1
    res_a = client.get("/patients/", headers=headers_a)
    assert res_a.status_code == 200
    patients_a = res_a.json()
    assert len(patients_a) > 0
    
    # Try to access a specific patient from Org A
    patient_a_id = patients_a[0]["id"]
    res_single_a = client.get(f"/patients/{patient_a_id}", headers=headers_a)
    assert res_single_a.status_code == 200
    assert "id" in res_single_a.json()

    # Create mock doctor token for Org 2
    token_doc_b = create_access_token(data={"sub": "dr_smith_2", "role": "doctor", "organization_id": 2})
    headers_b = {"Authorization": f"Bearer {token_doc_b}"}

    # Try to access Patient A using Doctor B's token
    res_hack = client.get(f"/patients/{patient_a_id}", headers=headers_b)
    assert res_hack.status_code == 403
    assert "does not belong to your organization" in res_hack.json()["detail"]
