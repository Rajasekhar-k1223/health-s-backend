from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class ApiKey(Base):
    """API Keys for external integrations (Developer Portal)."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    scopes = Column(String(500), default="READ_ONLY") # READ_ONLY, FULL_ACCESS, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

class Webhook(Base):
    """Webhooks for push notifications and external integrations."""
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    name = Column(String(255), nullable=False)
    endpoint_url = Column(String(500), nullable=False)
    events = Column(JSON, nullable=False) # e.g., ["Patient.Created", "Alert.Triggered"]
    secret = Column(String(255), nullable=True) # Used for signing payloads
    is_active = Column(Boolean, default=True)
