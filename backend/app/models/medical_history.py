from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, Enum
from sqlalchemy.orm import relationship
import enum
from .base import Base

class HistoryStatusEnum(str, enum.Enum):
    active = "active"
    resolved = "resolved"

class MedicalHistory(Base):
    __tablename__ = "medical_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    condition = Column(String(255), nullable=False)
    diagnosed_date = Column(Date, nullable=True)
    status = Column(Enum(HistoryStatusEnum), default=HistoryStatusEnum.active)
    notes = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="medical_history")
