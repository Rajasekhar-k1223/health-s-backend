from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base

class MedicationAdministration(Base):
    __tablename__ = "medication_administrations"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    medication_name = Column(String)
    dosage = Column(String)
    status = Column(String, default="completed") # in-progress, not-done, on-hold, completed, entered-in-error, stopped, unknown
    effective_time = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(Text, nullable=True)

    patient = relationship("Patient", backref="medication_administrations")
