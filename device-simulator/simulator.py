import requests
import time
import random
import json

API_URL = "http://localhost:8000"
TELEMETRY_ENDPOINT = f"{API_URL}/telemetry/ingest"

PATIENT_IDS = [1, 2, 3] # Demo patients
DEVICE_IDS = ["DEV-001", "DEV-002", "DEV-003"]

def generate_vitals():
    return {
        "heart_rate": random.randint(60, 100),
        "spo2": random.randint(95, 100),
        "temperature": round(random.uniform(36.5, 37.5), 1),
        "respiration_rate": random.randint(12, 20)
    }

# The API Gateway is now secured with JWTs
AUTH_ENDPOINT = f"{API_URL}/device-auth/token"

def get_jwt(serial, api_key):
    headers = {
        "X-Device-Serial": serial,
        "X-Device-API-Key": api_key
    }
    response = requests.post(AUTH_ENDPOINT, headers=headers)
    if response.status_code == 200:
        return response.json()["access_token"]
    print(f"Auth failed for {serial}")
    return None

def simulate_device(device_id, serial, api_key):
    print(f"Starting simulation for device {device_id} (Serial: {serial})")
    
    jwt_token = get_jwt(serial, api_key)
    if not jwt_token:
        return

    while True:
        patient_id = PATIENT_IDS[0]
        payload = {
            "device_id": device_id,
            "patient_id": patient_id,
            "vitals": generate_vitals(),
            "timestamp": time.time()
        }
        try:
            headers = {"Authorization": f"Bearer {jwt_token}"}
            requests.post(TELEMETRY_ENDPOINT, json=payload, headers=headers)
            print(f"Sent telemetry for {device_id}")
        except Exception as e:
            print(f"Failed to send telemetry for {device_id}: {e}")
        
        time.sleep(3)

if __name__ == "__main__":
    # In MVP, assume device 1 is assigned to patient 1, and device 1's serial is "SN-001" with API key "demo_key"
    simulate_device(device_id="DEV-001", serial="SN-001", api_key="demo_key")
