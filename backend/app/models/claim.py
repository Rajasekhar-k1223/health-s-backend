from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base

class ClaimStatus(str, enum.Enum):
    DRAFT = "Draft"
    PENDING = "Pending"
    PAID = "Paid"
    DENIED = "Denied"

class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String(100), unique=True, index=True, nullable=False)
    
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    coverage_id = Column(Integer, ForeignKey("coverages.id"), nullable=True)
    
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(ClaimStatus), default=ClaimStatus.PENDING)
    payer = Column(String(255), nullable=True) # E.g., Medicare, BlueCross
    
    fhir_id = Column(String(255), nullable=True)
    date_created = Column(DateTime(timezone=True), server_default=func.now())
    
    patient = relationship("Patient")
    encounter = relationship("Encounter")
    organization = relationship("Organization")
    coverage = relationship("Coverage")
