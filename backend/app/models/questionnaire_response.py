from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base

class QuestionnaireResponse(Base):
    __tablename__ = "questionnaire_responses"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    questionnaire_name = Column(String(255)) # e.g., PHQ-9
    status = Column(String(50), default="completed") # in-progress, completed, amended, entered-in-error, stopped
    authored = Column(DateTime, default=datetime.datetime.utcnow)
    answers = Column(JSON) # Store responses as JSON

    patient = relationship("Patient", backref="questionnaire_responses")
