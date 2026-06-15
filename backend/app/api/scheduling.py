from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import datetime

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.scheduling import Schedule, Appointment

router = APIRouter(prefix="/scheduling", tags=["scheduling"])

class ScheduleCreate(BaseModel):
    provider_id: int
    location_id: int
    start_time: datetime.datetime
    end_time: datetime.datetime

class AppointmentCreate(BaseModel):
    patient_id: int
    provider_id: int
    schedule_id: int
    type: str = "IN_PERSON"
    notes: str = None

@router.post("/schedules")
def create_schedule(
    sched: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor]))
):
    db_sched = Schedule(**sched.dict())
    db.add(db_sched)
    db.commit()
    db.refresh(db_sched)
    return db_sched

@router.post("/appointments")
def book_appointment(
    appt: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.nurse]))
):
    db_appt = Appointment(**appt.dict())
    db.add(db_appt)
    db.commit()
    db.refresh(db_appt)
    return db_appt

@router.get("/appointments/all")
def get_all_appointments(
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return db.query(Appointment).order_by(Appointment.id.desc()).limit(200).all()

@router.get("/appointments/patient/{patient_id}")
def get_patient_appointments(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return db.query(Appointment).filter(Appointment.patient_id == patient_id).all()

@router.delete("/appointments/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    db.delete(appt)
    db.commit()
    return {"message": "Appointment cancelled"}

