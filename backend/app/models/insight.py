from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class Insight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    risk_category = Column(String(50), nullable=False) # heart, respiratory, fever, fall, sleep
    score = Column(Float, nullable=False)
    summary = Column(Text, nullable=False)
    is_reviewed = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient")
