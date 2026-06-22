from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Task(Base):
    """Clinical or follow-up tasks."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(String(500), nullable=False)
    status = Column(String(50), default="PENDING") # PENDING, IN_PROGRESS, COMPLETED
    due_date = Column(DateTime, nullable=True)
    source = Column(String(100), nullable=True) # e.g., ALERT, MANUAL, CARE_PLAN

    patient = relationship("Patient", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id])

class WorkflowRule(Base):
    """Rule-based automation engine rules."""
    __tablename__ = "workflow_rules"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True) # Optional for global rules
    name = Column(String(255), nullable=False)
    trigger_event = Column(String(100), nullable=False) # e.g., LOW_SPO2, MISSED_MEDICATION
    condition_json = Column(JSON, nullable=True)
    action_json = Column(JSON, nullable=False) # e.g., {"action": "CREATE_TASK", "assignee_role": "DOCTOR"}
    status = Column(String(50), default="ACTIVE")
