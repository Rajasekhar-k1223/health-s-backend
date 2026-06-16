from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import Base

class PrescriptionStatus(str, enum.Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    EXPIRED = "Expired"
    REFILL_DUE = "Refill Due"

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    prescriber_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    drug_name = Column(String(255), nullable=False)
    sig = Column(String(500), nullable=False) # Patient instructions
    refills = Column(Integer, default=0)
    status = Column(Enum(PrescriptionStatus), default=PrescriptionStatus.ACTIVE)
    
    date_prescribed = Column(DateTime, default=datetime.utcnow)
    fhir_id = Column(String(255), nullable=True) # ID returned from the FHIR server
    
    patient = relationship("Patient")
    prescriber = relationship("User", foreign_keys=[prescriber_id])
