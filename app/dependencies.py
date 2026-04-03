from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import decode_token, is_token_revoked
from app import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    if is_token_revoked(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(models.User).filter(
        models.User.username == payload.get("sub")
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def require_analyst_or_admin(current_user=Depends(get_current_user)):
    if current_user.role not in [models.UserRole.analyst, models.UserRole.admin]:
        raise HTTPException(status_code=403, detail="Analyst or Admin access required")
    return current_user