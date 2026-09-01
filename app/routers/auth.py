from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas import LoginRequest, Token
from app.auth import verify_password, hash_password, create_access_token, decode_token
from app.database import get_db
from app.audit import log_audit_action
import os

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


@router.post("/login", response_model=Token)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    if body.username != ADMIN_USERNAME or body.password != ADMIN_PASSWORD:
        log_audit_action(
            db, username=body.username, action="LOGIN_FAILED",
            resource_type="auth", ip_address=request.client.host if request.client else None
        )
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = create_access_token({"sub": body.username, "role": "admin"})
    log_audit_action(
        db, username=body.username, action="LOGIN_SUCCESS",
        resource_type="auth", ip_address=request.client.host if request.client else None
    )
    return {"access_token": token, "token_type": "bearer"}



def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="No autenticado")
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return payload
