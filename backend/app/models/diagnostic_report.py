from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class DiagnosticReport(Base):
    __tablename__ = "diagnostic_reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True)
    
    test_name = Column(String(255), nullable=False) # e.g., Comprehensive Metabolic Panel
    status = Column(String(50), default="registered") # registered, partial, preliminary, final, amended, cancelled
    
    conclusion = Column(Text, nullable=True) # Overall clinical conclusion/interpretation
    result_value = Column(String(255), nullable=True) # E.g., Normal, Elevated, 8.2%
    
    issued_date = Column(DateTime(timezone=True), server_default=func.now())
    
    fhir_id = Column(String(255), nullable=True)
    
    patient = relationship("Patient")
    encounter = relationship("Encounter")
