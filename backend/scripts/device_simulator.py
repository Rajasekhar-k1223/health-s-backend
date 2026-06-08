import asyncio
import aiohttp
import json
import random
import math
from datetime import datetime, timezone
import argparse

API_URL = "http://localhost:8000/telemetry/ingest"

class DeviceSimulator:
    def __init__(self, device_id: str, api_key: str):
        self.device_id = device_id
        self.api_key = api_key
        
        # Base physiological baseline
        self.base_hr = random.uniform(60, 85)
        self.base_spo2 = random.uniform(96, 99)
        self.base_temp = random.uniform(98.0, 99.1)
        self.base_resp = random.uniform(12, 18)
        
        self.tick = 0

    def generate_ecg_waveform(self) -> list:
        # Simulate a quick 1-second ECG sample array (e.g. 100 Hz = 100 samples)
        # Using a simplified synthetic PQRST complex logic
        waveform = []
        for i in range(100):
            t = (self.tick * 100 + i) % 100
            val = 0.0
            if t == 10: val = 0.15 # P wave
            elif t == 25: val = -0.1 # Q wave
            elif t == 28: val = 1.0 # R wave
            elif t == 32: val = -0.2 # S wave
            elif t == 55: val = 0.25 # T wave
            else:
                val = random.uniform(-0.02, 0.02) # Baseline noise
            waveform.append(round(val, 3))
        return waveform

    def generate_metrics(self):
        self.tick += 1
        
        # Add random walk noise
        self.base_hr = max(40, min(200, self.base_hr + random.uniform(-1, 1)))
        self.base_spo2 = max(80, min(100, self.base_spo2 + random.uniform(-0.2, 0.2)))
        self.base_temp = max(95, min(105, self.base_temp + random.uniform(-0.05, 0.05)))
        self.base_resp = max(8, min(40, self.base_resp + random.uniform(-0.5, 0.5)))
        
        # Simulate a random fall (1 in 500 chance per tick)
        motion_status = "FALL_DETECTED" if random.random() < 0.002 else "NORMAL"
        
        return [
            {"type": "HR", "value": round(self.base_hr, 1), "unit": "bpm"},
            {"type": "SPO2", "value": round(self.base_spo2, 1), "unit": "%"},
            {"type": "TEMP", "value": round(self.base_temp, 1), "unit": "F"},
            {"type": "RESP", "value": round(self.base_resp, 1), "unit": "rpm"},
            {"type": "MOTION", "value": 1 if motion_status == "FALL_DETECTED" else 0, "unit": "alert"},
            {"type": "ECG", "value": self.generate_ecg_waveform(), "unit": "mV"}
        ]

    async def run(self):
        print(f"🚀 Starting Simulator for Device: {self.device_id}")
        
        async with aiohttp.ClientSession() as session:
            while True:
                payload = {
                    "device_id": self.device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metrics": self.generate_metrics()
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "x-device-id": self.device_id,
                    "x-api-key": self.api_key
                }
                
                try:
                    async with session.post(API_URL, json=payload, headers=headers) as resp:
                        if resp.status == 200:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {self.device_id}: Sent {len(payload['metrics'])} metrics")
                        else:
                            text = await resp.text()
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {self.device_id}: Error {resp.status} - {text}")
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 {self.device_id}: Connection failed - {str(e)}")
                    
                await asyncio.sleep(1.0) # 1 Hz telemetry tick

async def main():
    parser = argparse.ArgumentParser(description="Sentinel HealthOS Device Simulator")
    parser.add_argument("--device", required=True, help="Registered Device ID")
    parser.add_argument("--key", required=True, help="Device API Key")
    args = parser.parse_args()
    
    sim = DeviceSimulator(args.device, args.key)
    await sim.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulator stopped.")
