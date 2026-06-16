from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base

class ConsentStatus(str, enum.Enum):
    ACTIVE = "active"
    REJECTED = "rejected"
    REVOKED = "revoked"
    DRAFT = "draft"

class Consent(Base):
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(ConsentStatus), default=ConsentStatus.ACTIVE)
    category = Column(String(100), default="hipaa-notice") # e.g., hipaa-notice, data-sharing, research
    
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    policy_rule = Column(String(255), nullable=True) # URL or reference to the policy
    provision_type = Column(String(50), default="permit") # permit or deny
    
    date_signed = Column(DateTime(timezone=True), server_default=func.now())
    
    fhir_id = Column(String(255), nullable=True)
    
    patient = relationship("Patient")
    organization = relationship("Organization")
