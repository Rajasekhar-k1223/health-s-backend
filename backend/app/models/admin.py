from sqlalchemy import Column, String
from .base import Base

class AdminBase(Base):
    __abstract__ = True
    id = Column(String(36), primary_key=True, index=True)
    identifier = Column(String(255))
    status = Column(String(50))
    created_at = Column(String(100))

class Practitioner(AdminBase):
    __tablename__ = "practitioner"

class AdminOrganization(AdminBase):
    __tablename__ = "organization"

class AdminLocation(AdminBase):
    __tablename__ = "location"

class HealthcareService(AdminBase):
    __tablename__ = "healthcareservice"

class Account(AdminBase):
    __tablename__ = "account"

class AdminClaim(AdminBase):
    __tablename__ = "claim"

class AdminInvoice(AdminBase):
    __tablename__ = "invoice"

class AdminChargeItem(AdminBase):
    __tablename__ = "chargeitem"

class AdminCoverage(AdminBase):
    __tablename__ = "coverage"

class EligibilityRequest(AdminBase):
    __tablename__ = "eligibilityrequest"

class EligibilityResponse(AdminBase):
    __tablename__ = "eligibilityresponse"

class ExplanationOfBenefit(AdminBase):
    __tablename__ = "explanationofbenefit"
