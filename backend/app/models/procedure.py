from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base

class Procedure(Base):
    __tablename__ = "procedures"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    procedure_code = Column(String(50)) # e.g., CPT code
    procedure_name = Column(String(255))
    performed_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), default="completed") # preparation, in-progress, not-done, on-hold, stopped, completed, entered-in-error, unknown
    notes = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="procedures")
