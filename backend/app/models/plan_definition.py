from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base

class PlanDefinition(Base):
    __tablename__ = "plan_definitions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    title = Column(String) # e.g., "Drug Interaction Alert"
    description = Column(Text)
    status = Column(String, default="active") # active, draft, retired, unknown
    date_created = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", backref="plan_definitions")
