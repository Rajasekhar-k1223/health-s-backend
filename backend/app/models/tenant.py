from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Organization(Base):
    """Represents a Hospital Network or Healthcare Provider Tenant."""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tax_id = Column(String(50), nullable=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    locations = relationship("Location", back_populates="organization")

class Location(Base):
    """Represents a physical clinic or hospital building."""
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    type = Column(String(100), default="CLINIC") # HOSPITAL, CLINIC, PHARMACY
    status = Column(String(50), default="ACTIVE")

    organization = relationship("app.models.tenant.Organization", back_populates="locations")
    departments = relationship("Department", back_populates="location")

class Department(Base):
    """Represents a specialty department within a Location."""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    specialty = Column(String(100), nullable=True) # CARDIOLOGY, EMERGENCY, etc.

    location = relationship("Location", back_populates="departments")
