import sys
import os
import time
import random
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from faker import Faker

# Add the backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal, engine
from app.models import user, refresh_token, ward, care_team, patient, device, alert, audit, insight, note, device_auth, ota, document, clinical_note, security, tenant, scheduling, workflow, developer, medical_history
from app.models.tenant import Organization
from app.models.user import User, RoleEnum
from app.models.patient import Patient
from app.models.medical_history import MedicalHistory
from app.core.security import get_password_hash

fake = Faker()
FHIR_URL = "http://localhost:8080/fhir"

NUM_USERS = 500
NUM_PATIENTS = 9500 # Total 10k records

def generate_users(db, org_id, hashed_pw):
    print(f"Generating {NUM_USERS} user logins...")
    users = []
    
    roles = [RoleEnum.doctor, RoleEnum.nurse, RoleEnum.hospital_admin]
    weights = [0.6, 0.35, 0.05] # mostly doctors and nurses
    
    for i in range(NUM_USERS):
        role = random.choices(roles, weights=weights)[0]
        # create unique email
        email = f"{fake.user_name()}_{i}@sentinel.health"
        
        users.append(User(
            username=email,
            hashed_password=hashed_pw,
            role=role,
            organization_id=org_id,
            is_active=True
        ))
        
    db.add_all(users)
    db.commit()
    print("Users generated successfully.")

def sync_patient_to_fhir(p):
    """Sync a single patient to local HAPI FHIR server"""
    payload = {
        "resourceType": "Patient",
        "id": f"patient-{p.id}",
        "active": True,
        "name": [
            {
                "use": "official",
                "family": p.last_name,
                "given": [p.first_name]
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": p.contact_number
            }
        ],
        "gender": p.gender.lower() if p.gender else "unknown",
        "birthDate": p.dob.strftime("%Y-%m-%d") if p.dob else None
    }
    
    try:
        requests.put(f"{FHIR_URL}/Patient/{payload['id']}", json=payload, headers={"Content-Type": "application/fhir+json"}, timeout=2)
    except:
        pass # Ignore FHIR errors for bulk test if server is overwhelmed

def generate_patients(db, org_id):
    print(f"Generating {NUM_PATIENTS} patients and medical histories...")
    
    batch_size = 1000
    total_inserted = 0
    
    for batch in range(0, NUM_PATIENTS, batch_size):
        patients = []
        for i in range(batch_size):
            dob = fake.date_of_birth(minimum_age=18, maximum_age=90)
            p = Patient(
                organization_id=org_id,
                mrn=f"MRN-{fake.unique.random_int(min=1000000, max=9999999)}",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                dob=dob,
                age=(time.localtime().tm_year - dob.year),
                gender=random.choice(["Male", "Female", "Other"]),
                contact_number=fake.phone_number(),
                address=fake.address().replace("\n", ", "),
            )
            patients.append(p)
            
        db.add_all(patients)
        db.commit() # commit to get IDs
        
        histories = []
        for p in patients:
            # Generate random medical history gaps
            has_diabetes = random.choice([True, False])
            has_hypertension = random.choice([True, False])
            
            conditions = []
            if has_diabetes: conditions.append("Type 2 Diabetes")
            if has_hypertension: conditions.append("Hypertension")
            if not conditions and random.choice([True, False]): conditions.append("Healthy")
            
            mh = MedicalHistory(
                patient_id=p.id,
                condition=", ".join(conditions),
                notes="Generated during bulk insert. Allergies: None.",
                status="active"
            )
            histories.append(mh)
            
        db.add_all(histories)
        db.commit()
        
        # Sync this batch to FHIR concurrently
        print(f"Syncing batch of {batch_size} patients to FHIR...")
        with ThreadPoolExecutor(max_workers=50) as executor:
            executor.map(sync_patient_to_fhir, patients)
            
        total_inserted += batch_size
        print(f"Inserted {total_inserted}/{NUM_PATIENTS} patients.")
        
    print("Patients generated successfully.")

def bulk_seed():
    db = SessionLocal()
    start_time = time.time()
    try:
        # 1. Create Organization
        org = db.query(Organization).filter(Organization.name == "Global Health Network").first()
        if not org:
            org = Organization(name="Global Health Network", status="ACTIVE")
            db.add(org)
            db.commit()
            db.refresh(org)
            
        # 2. Hash password once for all users
        hashed_pw = get_password_hash("Password123!")
        
        # 3. Generate Users
        generate_users(db, org.id, hashed_pw)
        
        # 4. Generate Patients
        generate_patients(db, org.id)
        
        elapsed = time.time() - start_time
        print(f"Bulk Generation Complete in {elapsed:.2f} seconds!")
    finally:
        db.close()

if __name__ == "__main__":
    bulk_seed()
