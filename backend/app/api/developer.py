from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import secrets
import hashlib

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.developer import ApiKey, Webhook

router = APIRouter(prefix="/developer", tags=["developer"])

class ApiKeyCreate(BaseModel):
    name: str
    scopes: str = "READ_ONLY"

class WebhookCreate(BaseModel):
    name: str
    endpoint_url: str
    events: list

@router.post("/keys")
def create_api_key(
    key_req: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    db_key = ApiKey(
        name=key_req.name,
        key_hash=key_hash,
        scopes=key_req.scopes
    )
    # Typically assign tenant_id from current_user
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    
    return {"id": db_key.id, "name": db_key.name, "raw_key": raw_key, "message": "Store this key safely. It will not be shown again."}

@router.post("/webhooks")
def create_webhook(
    webhook_req: WebhookCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    secret = secrets.token_hex(16)
    db_webhook = Webhook(
        name=webhook_req.name,
        endpoint_url=webhook_req.endpoint_url,
        events=webhook_req.events,
        secret=secret
    )
    db.add(db_webhook)
    db.commit()
    db.refresh(db_webhook)
    
    return db_webhook
