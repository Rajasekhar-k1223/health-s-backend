import csv
import random
import uuid
from datetime import datetime, timedelta

NUM_RECORDS = 1_000_000
PATIENTS_FILE = 'patients.csv'
DEVICES_FILE = 'devices.csv'
ALERTS_FILE = 'alerts.csv'

print(f"Generating {NUM_RECORDS} records for MySQL...")

# Using simple generation to be fast instead of Faker, as Faker can be slow for 1M records
first_names = ["John", "Jane", "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy", "Mallory", "Victor", "Peggy", "Trent"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson"]

with open(PATIENTS_FILE, 'w', newline='', encoding='utf-8') as f_pat, \
     open(DEVICES_FILE, 'w', newline='', encoding='utf-8') as f_dev, \
     open(ALERTS_FILE, 'w', newline='', encoding='utf-8') as f_alt:
     
    writer_pat = csv.writer(f_pat)
    writer_dev = csv.writer(f_dev)
    writer_alt = csv.writer(f_alt)

    start_date = datetime(1940, 1, 1)
    timestamp = datetime.now()

    for i in range(1, NUM_RECORDS + 1):
        if i % 100000 == 0:
            print(f"Generated {i} records...")
            
        # Patient
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        mrn = f"MRN-{i:07d}"
        dob = (start_date + timedelta(days=random.randint(0, 25000))).strftime('%Y-%m-%d')
        age = random.randint(18, 90)
        risk = round(random.uniform(0, 5), 2)
        priority = random.choice(["low", "medium", "high", "critical"])
        # id, mrn, first_name, last_name, dob, gender, contact_number, address, age, risk_score, priority, primary_doctor_id, user_id, ward_id, organization_id
        writer_pat.writerow([i, mrn, fname, lname, dob, "Male" if random.random() > 0.5 else "Female", "555-1234", "123 Main St", age, risk, priority, "\\N", "\\N", "\\N", "\\N"])

        # Device
        device_id = f"DEV-{uuid.uuid4().hex[:8].upper()}"
        device_type = random.choice(["watch", "patch", "bed_sensor"])
        # id, device_id, serial_number, model, firmware_version, ownership_status, device_type, status, patient_id, organization_id
        writer_dev.writerow([i, device_id, f"SN-{i}", "ModelX", "v1.0", "owned", device_type, "active", i, "\\N"])

        # Alert (1 alert per patient for simplicity)
        alert_type = random.choice(["Cardiac", "Respiratory", "Fever", "Fall"])
        severity = random.choice(["low", "medium", "high", "critical"])
        metric = "heart_rate" if alert_type == "Cardiac" else "spo2"
        # id, patient_id, device_id, alert_type, severity, severity_score, metric, value, message, ai_insight, is_acknowledged, acknowledged_by, is_resolved, resolved_by, resolved_at, resolution_notes, timestamp
        writer_alt.writerow([i, i, device_id, alert_type, severity, random.randint(10, 100), metric, 120.0, f"{alert_type} alert triggered", "\\N", 0, "\\N", 0, "\\N", "\\N", "\\N", timestamp.strftime('%Y-%m-%d %H:%M:%S')])

print("CSV files generated successfully.")
