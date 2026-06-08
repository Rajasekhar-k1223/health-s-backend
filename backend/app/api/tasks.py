from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import datetime

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.workflow import Task

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskCreate(BaseModel):
    patient_id: int
    assignee_id: int = None
    description: str
    due_date: datetime.datetime = None
    source: str = "MANUAL"

@router.post("/")
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/")
def list_tasks(
    status: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    # Typically filter by user's organization/tenant here
    return query.all()

@router.put("/{task_id}/complete")
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "COMPLETED"
    db.commit()
    return task
