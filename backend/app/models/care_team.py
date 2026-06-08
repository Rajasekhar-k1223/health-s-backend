from sqlalchemy import Column, Integer, ForeignKey, String
from .base import Base

class CareTeam(Base):
    __tablename__ = "care_teams"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False) # e.g. primary_doctor, attending_nurse, home_caregiver
