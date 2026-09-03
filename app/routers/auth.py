from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas import LoginRequest, Token
from app.auth import verify_password, hash_password, create_access_token, decode_token
from app.database import get_db
from app.audit import log_audit_action
import os

from app.models import User
from app.dependencies import seed_default_users, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


@router.post("/login", response_model=Token)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    seed_default_users(db)
    
    # 1. Buscar usuario en base de datos
    user = db.query(User).filter(User.username == body.username).first()
    
    is_valid = False
    if user and user.is_active:
        is_valid = verify_password(body.password, user.hashed_password)
    
    # Fallback para credenciales de entorno admin legacy si usuario no existe
    if not is_valid and body.username == ADMIN_USERNAME and body.password == ADMIN_PASSWORD:
        user = db.query(User).filter(User.username == "admin").first()
        is_valid = True

    if not is_valid or not user or not user.is_active:
        log_audit_action(
            db, username=body.username, action="LOGIN_FAILED",
            resource_type="auth", ip_address=request.client.host if request.client else None
        )
        raise HTTPException(status_code=401, detail="Credenciales incorrectas o usuario inactivo")

    # Mapear rol 'admin' legacy a 'superadmin' en token
    effective_role = "superadmin" if user.role in ["superadmin", "admin"] else "operator"
    
    token = create_access_token({
        "sub": user.username,
        "role": effective_role,
        "full_name": user.full_name or user.username
    })
    
    log_audit_action(
        db, username=user.username, action="LOGIN_SUCCESS",
        resource_type="auth", details={"role": effective_role},
        ip_address=request.client.host if request.client else None
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": effective_role,
        "username": user.username,
        "full_name": user.full_name or user.username
    }


def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    if not credentials:
        raise HTTPException(status_code=401, detail="No autenticado")
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("role") not in ["superadmin", "admin"]:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return payload
