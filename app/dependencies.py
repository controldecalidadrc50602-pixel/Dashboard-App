from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import decode_token, hash_password
import os

security = HTTPBearer(auto_error=False)


def get_username(user_obj) -> str:
    if hasattr(user_obj, "username") and user_obj.username:
        return user_obj.username
    if isinstance(user_obj, dict):
        return user_obj.get("sub", "admin")
    return "admin"


def seed_default_users(db: Session):
    """Inicializa los usuarios admin y operador iniciales en la base de datos si no existen."""
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                hashed_password=hash_password(os.getenv("ADMIN_PASSWORD", "admin123")),
                role="superadmin",
                full_name="Administrador Master",
                email="admin@rc506.com",
                is_active=True
            )
            db.add(admin_user)

        operador_user = db.query(User).filter(User.username == "operador").first()
        if not operador_user:
            operador_user = User(
                username="operador",
                hashed_password=hash_password("rc506operador"),
                role="operator",
                full_name="Operador RC506",
                email="operador@rc506.com",
                is_active=True
            )
            db.add(operador_user)

        db.commit()
    except Exception as e:
        db.rollback()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta identificador de usuario"
        )
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        # Auto-seembrado de rescate si es el usuario admin por defecto
        if username == "admin":
            seed_default_users(db)
            user = db.query(User).filter(User.username == "admin").first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o no encontrado"
        )
    
    return user


def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol Super Admin"
        )
    return current_user


def require_operator_or_above(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["superadmin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado"
        )
    return current_user
