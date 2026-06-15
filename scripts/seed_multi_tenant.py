import os
import sys
from datetime import datetime, timezone
import random

# Add backend to path so we can import models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models import user, refresh_token, ward, care_team, patient, device, alert, audit, insight, note, device_auth, ota, document, clinical_note, security, tenant, scheduling, workflow, developer, medical_history
from app.models.user import User, RoleEnum
from app.models.tenant import Organization
from app.models.patient import Patient
from app.models.device import Device
from app.models.telehealth import TelehealthSession
from app.core.security import get_password_hash

def seed_database():
    print("Starting Multi-Tenant Database Seeding...")
    db = SessionLocal()
    try:
        # Create Tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # 1. Create Organizations (Hospitals)
        orgs_data = [
            {"name": "General Hospital Alpha"},
            {"name": "Mercy Clinic Beta"},
            {"name": "St. Jude Omega"}
        ]
        
        orgs = []
        for o in orgs_data:
            org = db.query(Organization).filter(Organization.name == o["name"]).first()
            if not org:
                org = Organization(name=o["name"])
                db.add(org)
                db.commit()
                db.refresh(org)
            orgs.append(org)
            
        print(f"Created {len(orgs)} Organizations.")

        # 2. Create Doctors for each Org
        doctors = []
        for i, org in enumerate(orgs):
            username = f"dr_smith_{i+1}"
            doc = db.query(User).filter(User.username == username).first()
            if not doc:
                doc = User(
                    username=username,
                    hashed_password=get_password_hash("SecurePass123!"),
                    role=RoleEnum.doctor,
                    organization_id=org.id,
                    is_active=True
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)
            doctors.append(doc)
            
        print(f"Created {len(doctors)} Doctors.")

        # 3. Create Patients & Devices
        patients = []
        for i in range(15): # 5 patients per org
            org = orgs[i % len(orgs)]
            doc = doctors[i % len(doctors)]
            
            mrn = f"MRN-SEED-{1000+i}"
            p = db.query(Patient).filter(Patient.mrn == mrn).first()
            if not p:
                p = Patient(
                    first_name=f"Patient{i}",
                    last_name="Test",
                    age=random.randint(20, 80),
                    organization_id=org.id,
                    user_id=None,
                    mrn=mrn
                )
                db.add(p)
                db.commit()
                db.refresh(p)
            patients.append(p)
            
            # Link a Device
            dev_id = f"DEV-{1000+i}"
            d = db.query(Device).filter(Device.device_id == dev_id).first()
            if not d:
                d = Device(
                    device_type="Bedside Monitor",
                    device_id=dev_id,
                    patient_id=p.id,
                    organization_id=org.id,
                    status="online"
                )
                db.add(d)
                db.commit()
            
            # Telehealth Session
            ts = TelehealthSession(
                doctor_id=doc.id,
                patient_id=p.id,
                status="completed",
                scheduled_time=datetime.now(timezone.utc),
                transcription="Patient reports mild headache and fatigue.",
                ai_summary="Assessment: Viral syndrome. Plan: Rest and fluids."
            )
            db.add(ts)
            
        db.commit()
        print(f"Created {len(patients)} Patients, Devices, and Telehealth Sessions.")
        print("Database successfully seeded with Multi-Tenant Data!")

    except Exception as e:
        print(f"Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
