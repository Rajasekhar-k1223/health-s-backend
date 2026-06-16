from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class ClaimResponse(Base):
    __tablename__ = "claim_responses"

    id = Column(Integer, primary_key=True, index=True)
    
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    
    outcome = Column(String(50), nullable=False) # E.g., complete, error, partial
    disposition = Column(String(255), nullable=True) # Text description of the outcome
    
    paid_amount = Column(Numeric(10, 2), default=0.0)
    denied_reason = Column(Text, nullable=True)
    
    fhir_id = Column(String(255), nullable=True)
    date_created = Column(DateTime(timezone=True), server_default=func.now())
    
    claim = relationship("Claim", backref="responses")
    patient = relationship("Patient")
