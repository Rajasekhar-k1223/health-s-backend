from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base

class FamilyHistory(Base):
    __tablename__ = "family_histories"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    relationship_code = Column(String(50))  # e.g., FTH (father), MTH (mother)
    condition_name = Column(String(255))
    notes = Column(Text, nullable=True)
    date_recorded = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="family_histories")
