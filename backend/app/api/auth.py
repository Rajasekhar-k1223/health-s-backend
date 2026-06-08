from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_user, require_role, get_password_hash
from app.models.user import User, RoleEnum
from app.models.refresh_token import RefreshToken
from app.models.audit import AuditLog

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_TOKEN_EXPIRE_DAYS = 7

@router.post("/login")
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # Audit log entry for attempt
    audit = AuditLog(username=form_data.username, action="LOGIN_ATTEMPT", resource="/auth/login")
    db.add(audit)
    db.commit()

    if not user or not verify_password(form_data.password, user.hashed_password):
        audit.action = "LOGIN_FAILED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Generate Access Token
    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}, expires_delta=access_token_expires
    )
    
    # Generate Refresh Token
    refresh_token_str = str(uuid.uuid4())
    refresh_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=refresh_expires
    )
    db.add(db_refresh_token)
    
    # Log success
    audit.action = "LOGIN_SUCCESS"
    db.commit()

    # Set HTTP-only cookie for refresh token
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_str,
        httponly=True,
        secure=True, 
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@router.post("/refresh")
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    db_token = db.query(RefreshToken).filter(RefreshToken.token == token, RefreshToken.revoked == False).first()
    
    if not db_token or db_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or deleted")

    # Generate new access token
    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if token:
        db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        if db_token:
            db_token.revoked = True
            db.commit()
            
    response.delete_cookie("refresh_token")
    return {"status": "logged out"}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active
    }
