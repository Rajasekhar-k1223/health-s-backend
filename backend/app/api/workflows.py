from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import json

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.workflow import WorkflowRule

router = APIRouter(prefix="/workflows", tags=["workflows"])

class WorkflowRuleCreate(BaseModel):
    name: str
    tenant_id: int = None
    trigger_event: str
    condition_json: dict = None
    action_json: dict

@router.post("/rules")
def create_workflow_rule(
    rule: WorkflowRuleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    db_rule = WorkflowRule(
        name=rule.name,
        tenant_id=rule.tenant_id,
        trigger_event=rule.trigger_event,
        condition_json=rule.condition_json,
        action_json=rule.action_json
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@router.get("/rules")
def list_workflow_rules(
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    return db.query(WorkflowRule).all()
