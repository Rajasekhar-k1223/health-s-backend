from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    device_id = Column(String(50), nullable=False)
    alert_type = Column(String(50), nullable=False) # Cardiac, Respiratory, Fever, Fall, Device Failure
    severity = Column(String(20), nullable=False) # low, medium, high, critical
    severity_score = Column(Integer, nullable=True) # 1-100 AI score
    metric = Column(String(50), nullable=False) # heart_rate, spo2, etc.
    value = Column(Float, nullable=False)
    message = Column(String(255), nullable=False)
    ai_insight = Column(String(1000), nullable=True)
    
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(String(1000), nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
    resolver = relationship("User", foreign_keys=[resolved_by])
