from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum
from datetime import datetime

router = APIRouter(prefix="/messaging", tags=["messaging"])

MOCK_THREADS = [
    { "id": 1, "from": "Dr. Mehta", "subject": "Patient MRN-5512 — Carvedilol concern", "preview": "Noticed Mason's adherence dropped to 60% this week…", "time": "2m ago", "unread": True },
    { "id": 2, "from": "RN Lina Park", "subject": "BP Alert — Room 4B", "preview": "Patient Owen Reyes has a reading of 180/110…", "time": "15m ago", "unread": True },
    { "id": 3, "from": "Dr. Shah", "subject": "Telehealth follow-up notes", "preview": "Attached the SOAP note from today's session…", "time": "1h ago", "unread": False },
    { "id": 4, "from": "Dr. Reyes", "subject": "Care plan update needed", "preview": "Can you review Priya's updated care plan before…", "time": "3h ago", "unread": False },
    { "id": 5, "from": "System", "subject": "OTA firmware update ready", "preview": "Device SN-003 has a pending firmware update…", "time": "1d ago", "unread": False }
]

MOCK_MESSAGES = {
    1: [
        { "from": "Dr. Mehta", "body": "Noticed Mason's adherence dropped to 60% this week. Should we schedule a pharmacy consult?", "time": "2m ago" },
        { "from": "You", "body": "Yes, good catch. I'll send a referral now and update the care plan.", "time": "1m ago", "self": True }
    ],
    2: [
        { "from": "RN Lina Park", "body": "Patient Owen Reyes has a reading of 180/110. He's in room 4B and says he feels dizzy.", "time": "15m ago" },
        { "from": "You", "body": "I'm coming now. Please prepare an IV line and get an ECG.", "time": "12m ago", "self": True },
        { "from": "RN Lina Park", "body": "Done. He's stable. ECG looks normal.", "time": "10m ago" }
    ]
}

@router.get("/threads", response_model=List[Dict[str, Any]])
def get_threads(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return MOCK_THREADS

@router.get("/threads/{thread_id}/messages", response_model=List[Dict[str, Any]])
def get_messages(
    thread_id: int,
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return MOCK_MESSAGES.get(thread_id, [])

@router.post("/threads/{thread_id}/messages", response_model=Dict[str, Any])
def post_message(
    thread_id: int,
    payload: Dict[str, Any],
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    new_msg = { "from": "You", "body": payload.get("body", ""), "time": "now", "self": True }
    if thread_id in MOCK_MESSAGES:
        MOCK_MESSAGES[thread_id].append(new_msg)
    else:
        MOCK_MESSAGES[thread_id] = [new_msg]
    return new_msg

@router.post("/threads", response_model=Dict[str, Any])
def create_thread(
    payload: Dict[str, Any],
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    new_thread = {
        "id": int(datetime.utcnow().timestamp()),
        "from": payload.get("to"),
        "subject": payload.get("subject"),
        "preview": payload.get("body", "")[:60],
        "time": "now",
        "unread": False
    }
    MOCK_THREADS.insert(0, new_thread)
    MOCK_MESSAGES[new_thread["id"]] = [{ "from": "You", "body": payload.get("body", ""), "time": "now", "self": True }]
    return new_thread

import requests
from pydantic import BaseModel
FHIR_URL = "http://localhost:8080/fhir"

class MaterialDelivery(BaseModel):
    patient_id: int
    material_title: str
    delivery_method: str # "sms" or "portal"

@router.post("/send-material")
def send_patient_material(
    payload: MaterialDelivery,
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    # Mock Twilio/Portal delivery
    print(f"Mocking {payload.delivery_method} delivery to patient {payload.patient_id}: {payload.material_title}")

    # FHIR CommunicationRequest
    fhir_payload = {
        "resourceType": "CommunicationRequest",
        "status": "active",
        "subject": { "reference": f"Patient/patient-{payload.patient_id}" },
        "requester": { "reference": f"Practitioner/user-{current_user.id}" },
        "payload": [
            { "contentString": f"Educational Material Sent: {payload.material_title} via {payload.delivery_method}" }
        ],
        "authoredOn": datetime.utcnow().isoformat() + "Z"
    }

    try:
        response = requests.post(f"{FHIR_URL}/CommunicationRequest", json=fhir_payload, headers={"Content-Type": "application/fhir+json"})
        response.raise_for_status()
        return {"message": f"Material sent via {payload.delivery_method} and logged to FHIR"}
    except Exception as e:
        # Ignore for mock purposes if FHIR is down
        return {"message": f"Material sent via {payload.delivery_method}. (FHIR sync bypassed)"}
