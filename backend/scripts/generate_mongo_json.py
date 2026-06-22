import json
from datetime import datetime, timedelta
import random

NUM_RECORDS = 1_000_000
MONGO_FILE = 'telemetry.json'

print(f"Generating {NUM_RECORDS} records for MongoDB JSON import...")

start_date = datetime.utcnow() - timedelta(days=30)
metrics = ["HR", "SPO2", "TEMP", "RESP"]
units = {"HR": "bpm", "SPO2": "%", "TEMP": "C", "RESP": "rpm"}

with open(MONGO_FILE, 'w', encoding='utf-8') as f:
    for i in range(NUM_RECORDS):
        if i % 100000 == 0:
            print(f"Generated {i} MongoDB records...")
            
        metric_type = random.choice(metrics)
        doc = {
            "device_id": f"DEV-{random.randint(1, 100000)}",
            "patient_id": random.randint(1, 100000),
            "timestamp": (start_date + timedelta(seconds=random.randint(0, 2592000))).isoformat() + "Z",
            "type": metric_type,
            "value": round(random.uniform(60, 100) if metric_type in ["HR", "SPO2"] else random.uniform(36, 40), 2),
            "unit": units[metric_type]
        }
        f.write(json.dumps(doc) + "\n")

print("MongoDB JSON file generated successfully.")
