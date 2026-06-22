import pymongo
from datetime import datetime, timedelta
import random

MONGO_URI = "mongodb://root:rootpassword@localhost:27017/?authSource=admin"
DB_NAME = "sentinel"
COLLECTION_NAME = "telemetry"

NUM_RECORDS = 1_000_000
BATCH_SIZE = 50_000

print(f"Connecting to MongoDB at {MONGO_URI}...")
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

print(f"Generating {NUM_RECORDS} records for MongoDB in batches of {BATCH_SIZE}...")

start_date = datetime.utcnow() - timedelta(days=30)
metrics = ["HR", "SPO2", "TEMP", "RESP"]
units = {"HR": "bpm", "SPO2": "%", "TEMP": "C", "RESP": "rpm"}

total_inserted = 0
while total_inserted < NUM_RECORDS:
    batch = []
    for i in range(BATCH_SIZE):
        metric_type = random.choice(metrics)
        doc = {
            "device_id": f"DEV-{random.randint(1, 100000)}",
            "patient_id": random.randint(1, 100000),
            "timestamp": start_date + timedelta(seconds=random.randint(0, 2592000)),
            "type": metric_type,
            "value": round(random.uniform(60, 100) if metric_type in ["HR", "SPO2"] else random.uniform(36, 40), 2),
            "unit": units[metric_type]
        }
        batch.append(doc)
    
    collection.insert_many(batch)
    total_inserted += len(batch)
    print(f"Inserted {total_inserted}/{NUM_RECORDS} telemetry records...")

print("MongoDB bulk data generation complete.")
