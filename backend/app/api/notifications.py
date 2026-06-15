from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import time

from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/notifications", tags=["notifications"])

class NotificationRequest(BaseModel):
    user_id: int
    channel: str # 'email', 'push', 'sms'
    subject: str
    message: str
    priority: str = "normal"

class NotificationResponse(BaseModel):
    id: str
    status: str
    timestamp: str

def mock_send_notification(req: NotificationRequest):
    # Mocking external API call (SendGrid, Twilio, APNs)
    time.sleep(1)
    print(f"[{req.channel.upper()}] Sent to User {req.user_id}: {req.subject}")

@router.post("/send", response_model=NotificationResponse)
def send_notification(
    req: NotificationRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    background_tasks.add_task(mock_send_notification, req)
    return NotificationResponse(
        id=f"notif-{int(time.time())}",
        status="queued",
        timestamp=str(time.time())
    )

@router.get("/preferences/{user_id}")
def get_notification_preferences(
    user_id: int,
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    return {
        "email_enabled": True,
        "push_enabled": True,
        "sms_enabled": False,
        "do_not_disturb": False
    }
