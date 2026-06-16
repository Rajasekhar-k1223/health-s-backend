from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base

class MedicationDispense(Base):
    __tablename__ = "medication_dispenses"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    medication_name = Column(String)
    quantity = Column(String)
    days_supply = Column(Integer, nullable=True)
    status = Column(String, default="completed") # preparation, in-progress, cancelled, on-hold, completed, entered-in-error, stopped, declined, unknown
    handed_over_date = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(Text, nullable=True)

    patient = relationship("Patient", backref="medication_dispenses")
