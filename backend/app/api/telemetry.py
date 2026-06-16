from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import hashlib
from pymongo import MongoClient
import os
import json
import asyncio

from app.core.database import get_db
from app.core.websocket import manager
from app.models.device import Device
from app.models.device_auth import DeviceCredential
from app.schemas.telemetry import TelemetryIngest, TelemetryDataDoc

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
try:
    mongo_client = MongoClient(MONGO_URI)
    db_mongo = mongo_client.healthos
    telemetry_collection = db_mongo.telemetry_data
except Exception as e:
    telemetry_collection = None
    print(f"Failed to connect to MongoDB: {e}")

def verify_device_token(x_device_id: str = Header(...), x_api_key: str = Header(...), db: Session = Depends(get_db)):
    """Authenticate incoming telemetry using API Keys."""
    device = db.query(Device).filter(Device.device_id == x_device_id).first()
    if not device or device.status != "active":
        raise HTTPException(status_code=401, detail="Invalid or inactive device")
        
    api_key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    cred = db.query(DeviceCredential).filter(
        DeviceCredential.device_id == device.id, 
        DeviceCredential.api_key_hash == api_key_hash,
        DeviceCredential.is_active == True
    ).first()
    
    if not cred:
        raise HTTPException(status_code=401, detail="Unauthorized device credentials")
        
    return device

def process_and_store_telemetry(payload: TelemetryIngest, patient_id: Optional[int]):
    """Background task to store telemetry to Timeseries DB (MongoDB)."""
    if not telemetry_collection:
        print(f"[MOCK TSDB] Stored Telemetry for {payload.device_id} (Patient {patient_id}) - {len(payload.metrics)} metrics")
    else:
        documents = []
        for metric in payload.metrics:
            doc = {
                "device_id": payload.device_id,
                "patient_id": patient_id,
                "timestamp": payload.timestamp,
                "type": metric.type,
                "value": metric.value,
                "unit": metric.unit
            }
            documents.append(doc)
            
        if documents:
            try:
                telemetry_collection.insert_many(documents)
                print(f"Stored {len(documents)} telemetry points to MongoDB for Device {payload.device_id}")
            except Exception as e:
                print(f"❌ Failed to insert telemetry into MongoDB: {e}")
                print(f"[FALLBACK TSDB] Telemetry logged for {payload.device_id} (Patient {patient_id}) without MongoDB persistence")
        
    if patient_id:
        try:
            from app.services.fhir_sync import sync_observation_to_fhir
            for metric in payload.metrics:
                # We skip ECG raw waveforms to prevent FHIR server bloat
                if metric.type == "ECG":
                    continue
                sync_observation_to_fhir(payload.device_id, patient_id, metric.type, metric.value, metric.unit)
        except Exception as e:
            print(f"🚨 Background FHIR observation sync failed: {e}")

@router.post("/ingest")
def ingest_telemetry(
    payload: TelemetryIngest, 
    background_tasks: BackgroundTasks,
    device: Device = Depends(verify_device_token)
):
    """
    High-throughput ingestion endpoint for IoT Devices.
    Verifies the device, unpacks metrics, and pushes them to the processing queue.
    """
    if payload.device_id != device.device_id:
        raise HTTPException(status_code=400, detail="Device ID mismatch")
        
    # Queue the heavy DB writes to background to keep the Gateway fast
    background_tasks.add_task(process_and_store_telemetry, payload, device.patient_id)
    
    # Broadcast to WebSocket clients immediately
    if device.patient_id:
        # Create an async task so we don't block the HTTP response
        asyncio.create_task(manager.broadcast_to_patient(device.patient_id, payload.dict()))
        # Also broadcast to central dashboard (listening on patient_id=0)
        asyncio.create_task(manager.broadcast_to_patient(0, {"patient_id": device.patient_id, "payload": payload.dict()}))
    
    return {"status": "received", "metrics_count": len(payload.metrics)}
