from sqlalchemy import Column, Integer, String, ForeignKey, Text, Enum, Date
from sqlalchemy.orm import relationship
import enum
from .base import Base

class CarePlanIntent(str, enum.Enum):
    PROPOSAL = "proposal"
    PLAN = "plan"
    ORDER = "order"

class CarePlan(Base):
    __tablename__ = "care_plans"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Doctor who created it
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    intent = Column(Enum(CarePlanIntent), default=CarePlanIntent.PLAN)
    status = Column(String(50), default="active") # active, completed, revoked
    
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    fhir_id = Column(String(255), nullable=True)
    
    patient = relationship("Patient")
    author = relationship("User")
