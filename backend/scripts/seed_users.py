import sys
import os
from pathlib import Path

# Add the backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models import user, refresh_token, ward, care_team, patient, device, alert, audit, insight, note, device_auth, ota, document, clinical_note, security, tenant, scheduling, workflow, developer, medical_history
from app.models.tenant import Organization
from app.models.user import User, RoleEnum
from app.core.security import get_password_hash

def seed():
    db = SessionLocal()
    try:
        # Create default organization if it doesn't exist
        org = db.query(Organization).filter(Organization.name == "Sentinel General Hospital").first()
        if not org:
            org = Organization(name="Sentinel General Hospital", status="ACTIVE")
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"Created Organization: {org.name} (ID: {org.id})")
        
        users_to_create = [
            # 1 Super Admin
            {"username": "superadmin@sentinel.health", "role": RoleEnum.super_admin, "org_id": None},
            
            # Multiple Org Admins
            {"username": "admin1@sentinel.health", "role": RoleEnum.hospital_admin, "org_id": org.id},
            {"username": "admin2@sentinel.health", "role": RoleEnum.hospital_admin, "org_id": org.id},
            
            # Multiple Doctors
            {"username": "dr.smith@sentinel.health", "role": RoleEnum.doctor, "org_id": org.id},
            {"username": "dr.jones@sentinel.health", "role": RoleEnum.doctor, "org_id": org.id},
            {"username": "dr.patel@sentinel.health", "role": RoleEnum.doctor, "org_id": org.id},
            
            # Multiple Nurses
            {"username": "nurse.claire@sentinel.health", "role": RoleEnum.nurse, "org_id": org.id},
            {"username": "nurse.joyce@sentinel.health", "role": RoleEnum.nurse, "org_id": org.id},
            
            # Multiple Patients
            {"username": "patient1@sentinel.health", "role": RoleEnum.patient, "org_id": org.id},
            {"username": "patient2@sentinel.health", "role": RoleEnum.patient, "org_id": org.id},
            {"username": "patient3@sentinel.health", "role": RoleEnum.patient, "org_id": org.id},
        ]

        default_password = "Password123!"
        hashed_pw = get_password_hash(default_password)

        for u in users_to_create:
            existing = db.query(User).filter(User.username == u["username"]).first()
            if not existing:
                new_user = User(
                    username=u["username"],
                    hashed_password=hashed_pw,
                    role=u["role"],
                    organization_id=u["org_id"],
                    is_active=True
                )
                db.add(new_user)
                print(f"Created User: {u['username']} with role {u['role']}")
            else:
                print(f"User already exists: {u['username']}")

        db.commit()
        print("Seeding complete!")
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting database seed...")
    seed()
