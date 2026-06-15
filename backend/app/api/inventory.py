from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("/stock", response_model=List[Dict[str, Any]])
def get_inventory_stock(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    return [
        {"item": "N95 Masks", "category": "PPE", "stock": 4500, "min": 1000, "status": "In Stock"},
        {"item": "IV Fluids (Saline 1L)", "category": "Supplies", "stock": 120, "min": 200, "status": "Low Stock"},
        {"item": "Syringes (10ml)", "category": "Supplies", "stock": 850, "min": 500, "status": "In Stock"},
        {"item": "Epinephrine Auto-Injectors", "category": "Medication", "stock": 5, "min": 20, "status": "Critical"}
    ]
