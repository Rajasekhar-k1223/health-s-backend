from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class Ward(Base):
    __tablename__ = "wards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False) # e.g. INPATIENT, HOME_MONITORING
    
    patients = relationship("Patient", back_populates="ward")
