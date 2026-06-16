from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base

class EncounterStatus(str, enum.Enum):
    PLANNED = "planned"
    ARRIVED = "arrived"
    TRIAGED = "triaged"
    IN_PROGRESS = "in-progress"
    ONLEAVE = "onleave"
    FINISHED = "finished"
    CANCELLED = "cancelled"

class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    
    status = Column(Enum(EncounterStatus), default=EncounterStatus.IN_PROGRESS)
    encounter_class = Column(String(50), default="AMB") # AMB (ambulatory), IMP (inpatient), EMER (emergency)
    
    start_time = Column(DateTime(timezone=True), default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    reason = Column(Text, nullable=True)
    
    patient = relationship("Patient", back_populates="encounters")
    doctor = relationship("User", back_populates="encounters")
    location = relationship("Location")
