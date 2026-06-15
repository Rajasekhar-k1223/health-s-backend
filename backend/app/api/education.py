from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.security import require_role
from app.models.user import RoleEnum

router = APIRouter(prefix="/education", tags=["education"])

MOCK_MODULES = [
    { "id": 1, "title": "Understanding Heart Failure", "category": "Cardiology", "duration": "12 min", "level": "Beginner", "assigned": 45, "completed": 32, "rating": 4.8 },
    { "id": 2, "title": "Managing Type 2 Diabetes Daily", "category": "Endocrinology", "duration": "18 min", "level": "Intermediate", "assigned": 89, "completed": 71, "rating": 4.9 },
    { "id": 3, "title": "COPD Breathing Techniques", "category": "Pulmonology", "duration": "15 min", "level": "Beginner", "assigned": 34, "completed": 20, "rating": 4.6 },
    { "id": 4, "title": "Medication Adherence Tips", "category": "General", "duration": "8 min", "level": "Beginner", "assigned": 120, "completed": 95, "rating": 4.7 },
    { "id": 5, "title": "Understanding Your Lab Results", "category": "General", "duration": "10 min", "level": "Beginner", "assigned": 67, "completed": 45, "rating": 4.5 },
    { "id": 6, "title": "Post-Surgery Recovery Guide", "category": "Surgical", "duration": "20 min", "level": "Intermediate", "assigned": 28, "completed": 22, "rating": 4.9 }
]

@router.get("/modules", response_model=List[Dict[str, Any]])
def get_modules(
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    return MOCK_MODULES

@router.post("/modules", response_model=Dict[str, Any])
def create_module(
    payload: Dict[str, Any],
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor]))
):
    new_module = {
        "id": len(MOCK_MODULES) + 1,
        "title": payload.get("title"),
        "category": payload.get("category", "General"),
        "duration": payload.get("duration", "10 min"),
        "level": payload.get("level", "Beginner"),
        "assigned": 0,
        "completed": 0,
        "rating": 0
    }
    MOCK_MODULES.append(new_module)
    return new_module
