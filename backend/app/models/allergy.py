from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Date
from sqlalchemy.orm import relationship
import enum
from .base import Base

class AllergySeverity(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"

class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    
    substance = Column(String(255), nullable=False) # e.g., Penicillin, Peanuts
    reaction = Column(String(255), nullable=True) # e.g., Hives, Anaphylaxis
    severity = Column(Enum(AllergySeverity), default=AllergySeverity.MODERATE)
    
    identified_date = Column(Date, nullable=True)
    status = Column(String(50), default="active") # active, inactive, resolved
    
    fhir_id = Column(String(255), nullable=True)
    
    patient = relationship("Patient")
