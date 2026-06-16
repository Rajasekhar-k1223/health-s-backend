from sqlalchemy import Column, Integer, String, ForeignKey, Float, Date, Text
from sqlalchemy.orm import relationship
from .base import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    mrn = Column(String(50), unique=True, index=True, nullable=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    dob = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    contact_number = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    age = Column(Integer, nullable=False)
    risk_score = Column(Float, default=0.0)
    priority = Column(String(20), default="low") # low, medium, high, critical
    
    primary_doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    devices = relationship("Device", back_populates="patient")
    ward = relationship("Ward", back_populates="patients")
    care_team = relationship("CareTeam", backref="patient")
    medical_history = relationship("MedicalHistory", back_populates="patient", cascade="all, delete-orphan")
    
    primary_doctor = relationship("User", foreign_keys=[primary_doctor_id])
    prescriptions = relationship("Prescription", back_populates="patient", cascade="all, delete-orphan")
    encounters = relationship("Encounter", back_populates="patient", cascade="all, delete-orphan")
    # Using string reference for Task to avoid circular import if task isn't imported
    tasks = relationship("Task", back_populates="patient", cascade="all, delete-orphan")
    
    immunizations = relationship("Immunization", back_populates="patient", cascade="all, delete-orphan")
    family_histories = relationship("FamilyHistory", back_populates="patient", cascade="all, delete-orphan")
    procedures = relationship("Procedure", back_populates="patient", cascade="all, delete-orphan")
