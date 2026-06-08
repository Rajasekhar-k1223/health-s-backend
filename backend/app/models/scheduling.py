from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Schedule(Base):
    """Provider availability schedule."""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    provider = relationship("User", foreign_keys=[provider_id])
    location = relationship("Location")

class Appointment(Base):
    """Booked appointment slot."""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    status = Column(String(50), default="BOOKED") # BOOKED, CANCELLED, COMPLETED
    type = Column(String(50), default="IN_PERSON") # IN_PERSON, TELEHEALTH
    notes = Column(String(500), nullable=True)

    patient = relationship("Patient")
    provider = relationship("User", foreign_keys=[provider_id])
    schedule = relationship("Schedule")


