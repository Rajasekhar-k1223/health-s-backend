from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
import enum
from sqlalchemy import Enum

class NoteStatus(str, enum.Enum):
    draft = "draft"
    finalized = "finalized"

class DoctorNote(Base):
    __tablename__ = "doctor_notes"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    action_item = Column(String(255), nullable=True) # e.g. "follow-up task"
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient")
    doctor = relationship("User")

