from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class SecurityThreat(Base):
    __tablename__ = "security_threats"

    id = Column(Integer, primary_key=True, index=True)
    threat_type = Column(String(50), nullable=False) # UNAUTHORIZED_ACCESS, DEVICE_ANOMALY, BRUTE_FORCE, PHI_EXFILTRATION
    severity = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=False)
    target_id = Column(String(100), nullable=True) # e.g. User ID, IP, or Device MAC
    status = Column(String(20), default="OPEN") # OPEN, INVESTIGATING, RESOLVED
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

class PatientConsent(Base):
    __tablename__ = "patient_consents"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    consent_type = Column(String(50), nullable=False) # TELEHEALTH, AI_ANALYSIS, DATA_SHARING, RESEARCH
    status = Column(String(20), default="GRANTED") # GRANTED, REVOKED
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patient = relationship("Patient", backref="consents")
