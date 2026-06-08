from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class ClinicalNote(Base):
    __tablename__ = "clinical_notes"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("telehealth_sessions.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note_type = Column(String(50), default="SOAP") # SOAP, General, Transcription
    content = Column(Text, nullable=False)
    signed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("TelehealthSession")
    patient = relationship("Patient")
    doctor = relationship("User")
