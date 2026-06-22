from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base

class Immunization(Base):
    __tablename__ = "immunizations"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    vaccine_code = Column(String(50))  # e.g., CVX code
    vaccine_name = Column(String(255))
    administered_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), default="completed") # completed, entered-in-error, not-done
    notes = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="immunizations")
