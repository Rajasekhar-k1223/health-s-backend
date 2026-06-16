from sqlalchemy import Column, Integer, String, ForeignKey, Date, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from .base import Base

class CoverageStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    DRAFT = "draft"
    ENTERED_IN_ERROR = "entered-in-error"

class Coverage(Base):
    __tablename__ = "coverages"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(CoverageStatus), default=CoverageStatus.ACTIVE)
    type = Column(String(50), nullable=True) # E.g., medical, dental, vision
    
    subscriber_id = Column(String(100), nullable=False) # Member ID
    group_number = Column(String(100), nullable=True)
    plan_name = Column(String(255), nullable=True)
    network_type = Column(String(50), nullable=True) # PPO, HMO, EPO
    
    payer_name = Column(String(255), nullable=False) # Insurance company name
    
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    
    fhir_id = Column(String(255), nullable=True)
    
    patient = relationship("Patient", backref="coverages")
