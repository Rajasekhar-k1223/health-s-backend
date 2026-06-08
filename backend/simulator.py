import os
import time
import math
import random
import requests
from datetime import datetime, timedelta
from jose import jwt

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
ALGORITHM = "HS256"

# Generate a Device JWT
def get_device_token(device_id: str):
    to_encode = {"sub": device_id, "type": "device", "exp": datetime.utcnow() + timedelta(days=1)}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def run_simulator():
    print("[START] Starting Sentinel HealthOS Device Simulator...")
    
    # We will simulate 3 specific devices
    devices = [
        {"id": "device_1", "base_hr": 75, "base_sp": 98},
        {"id": "device_2", "base_hr": 85, "base_sp": 96},
        {"id": "device_3", "base_hr": 125, "base_sp": 91, "critical": True}, # Simulating a critical patient
    ]

    tokens = {d["id"]: get_device_token(d["id"]) for d in devices}
    
    print(f"Generated tokens for {len(devices)} simulated devices.")
    print("Streaming telemetry to backend... Press Ctrl+C to stop.\n")

    tick = 0
    try:
        while True:
            for d in devices:
                # Add some sine wave variance
                hr_variance = math.sin(tick * 0.5) * 5
                sp_variance = math.cos(tick * 0.2) * 2
                
                # Add some random noise
                hr = int(d["base_hr"] + hr_variance + random.uniform(-2, 2))
                sp = min(100, int(d["base_sp"] + sp_variance + random.uniform(-1, 1)))
                
                # Create telemetry payload
                payload = {
                    "heart_rate": hr,
                    "spo2": sp,
                    "temperature": round(37.0 + random.uniform(-0.2, 0.2), 1),
                    "respiration_rate": int(16 + random.uniform(-2, 2)),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

                # Send to backend
                try:
                    headers = {"Authorization": f"Bearer {tokens[d['id']]}"}
                    response = requests.post(f"{API_URL}/telemetry/ingest", json=payload, headers=headers)
                    if response.status_code == 200:
                        status = "[OK]"
                    else:
                        status = f"[ERR {response.status_code}]"
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {status} Device {d['id']} -> HR: {hr} bpm | SpO2: {sp}%")
                except requests.exceptions.ConnectionError:
                    print(f"[ERR] Connection error. Is the backend running at {API_URL}?")

            tick += 1
            time.sleep(2) # Stream every 2 seconds
            
    except KeyboardInterrupt:
        print("\n[STOP] Simulator stopped.")

if __name__ == "__main__":
    run_simulator()
