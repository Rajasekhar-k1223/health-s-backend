from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class TelehealthSession(Base):
    __tablename__ = "telehealth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(String(20), default="scheduled") # scheduled, active, completed, cancelled
    type = Column(String(20), default="video") # video, audio, in-person
    meeting_url = Column(String(255), nullable=True)
    notes = Column(String(500), nullable=True)
    transcription = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", backref="telehealth_sessions")
    doctor = relationship("User", backref="telehealth_sessions")
