from pydantic import BaseModel
from typing import Optional
from app.models.user import RoleEnum

class UserBase(BaseModel):
    username: str
    role: RoleEnum

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
