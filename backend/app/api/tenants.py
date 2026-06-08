from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.tenant import Organization, Location, Department

router = APIRouter(prefix="/tenants", tags=["tenants"])

# Schemas
class OrganizationCreate(BaseModel):
    name: str
    tax_id: str = None

class LocationCreate(BaseModel):
    organization_id: int
    name: str
    address: str = None
    type: str = "CLINIC"

# Endpoints
@router.post("/organizations")
def create_organization(
    org: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin]))
):
    db_org = Organization(name=org.name, tax_id=org.tax_id)
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org

@router.get("/organizations")
def list_organizations(
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    return db.query(Organization).all()

@router.post("/locations")
def create_location(
    loc: LocationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin]))
):
    db_loc = Location(organization_id=loc.organization_id, name=loc.name, address=loc.address, type=loc.type)
    db.add(db_loc)
    db.commit()
    db.refresh(db_loc)
    return db_loc

@router.get("/organizations/{org_id}/locations")
def list_locations(
    org_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return db.query(Location).filter(Location.organization_id == org_id).all()
