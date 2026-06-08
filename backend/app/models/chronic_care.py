from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class CareProgram(Base):
    __tablename__ = "care_programs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    duration_days = Column(Integer, default=90)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProgramEnrollment(Base):
    __tablename__ = "program_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    program_id = Column(Integer, ForeignKey("care_programs.id"), nullable=False)
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="active") # active, graduated, dropped
    adherence_score = Column(Float, default=100.0)

    patient = relationship("Patient", backref="enrollments")
    program = relationship("CareProgram", backref="enrollments")
