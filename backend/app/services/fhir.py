import os
import requests
import datetime
from app.models.patient import Patient
from app.models.device import Device
from app.models.alert import Alert

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL", "http://localhost:8080/fhir")

def sync_patient(patient: Patient) -> str:
    fhir_patient = {
        "resourceType": "Patient",
        "name": [
            {
                "use": "official",
                "family": patient.last_name,
                "given": [patient.first_name]
            }
        ],
        "active": True
    }
    
    response = requests.post(f"{FHIR_SERVER_URL}/Patient", json=fhir_patient)
    response.raise_for_status()
    return response.json().get("id")

def sync_device(device: Device, fhir_patient_id: str = None) -> str:
    fhir_device = {
        "resourceType": "Device",
        "identifier": [
            {
                "system": "http://sentinel-healthos.com/devices",
                "value": device.device_id
            }
        ],
        "type": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "466056008",
                    "display": device.device_type
                }
            ]
        },
        "status": "active"
    }
    if fhir_patient_id:
        fhir_device["patient"] = {"reference": f"Patient/{fhir_patient_id}"}

    response = requests.post(f"{FHIR_SERVER_URL}/Device", json=fhir_device)
    response.raise_for_status()
    return response.json().get("id")

def sync_telemetry_observation(patient_id: str, device_id: str, metric_name: str, value: float, unit: str):
    """Sync a single vitals metric as a FHIR Observation"""
    code_map = {
        "heart_rate": {"code": "8867-4", "display": "Heart rate"},
        "spo2": {"code": "2708-6", "display": "Oxygen saturation in Arterial blood"},
        "temperature": {"code": "8310-5", "display": "Body temperature"},
        "respiration_rate": {"code": "9279-1", "display": "Respiratory rate"}
    }
    
    mapping = code_map.get(metric_name)
    if not mapping:
        return None
        
    fhir_observation = {
        "resourceType": "Observation",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": mapping["code"],
                    "display": mapping["display"]
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "device": {
            "reference": f"Device/{device_id}"
        },
        "effectiveDateTime": datetime.datetime.utcnow().isoformat() + "Z",
        "valueQuantity": {
            "value": value,
            "unit": unit,
            "system": "http://unitsofmeasure.org"
        }
    }
    
    response = requests.post(f"{FHIR_SERVER_URL}/Observation", json=fhir_observation)
    response.raise_for_status()
    return response.json().get("id")

def sync_alert_as_detected_issue(alert: Alert, fhir_patient_id: str):
    fhir_issue = {
        "resourceType": "DetectedIssue",
        "status": "final",
        "severity": alert.severity, # high, moderate, low
        "patient": {
            "reference": f"Patient/{fhir_patient_id}"
        },
        "detail": alert.message,
        "mitigation": [
            {
                "action": {
                    "text": "Clinical review recommended. This is not a diagnosis."
                }
            }
        ]
    }
    
    response = requests.post(f"{FHIR_SERVER_URL}/DetectedIssue", json=fhir_issue)
    response.raise_for_status()
    return response.json().get("id")
