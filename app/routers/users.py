from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserUpdate, UserOut
from app.dependencies import require_superadmin
from app.auth import hash_password
from app.audit import log_audit_action

router = APIRouter(prefix="/api/admin/users", tags=["users"])


@router.get("/", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_superadmin)
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_superadmin)
):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"El nombre de usuario '{body.username}' ya existe"
        )
    
    role = "superadmin" if body.role in ["superadmin", "admin"] else "operator"
    
    new_user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        role=role,
        full_name=body.full_name,
        email=body.email,
        is_active=body.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit_action(
        db,
        username=admin.username,
        action="CREATE_USER",
        resource_type="user",
        resource_id=str(new_user.id),
        details={"username": new_user.username, "role": new_user.role}
    )

    return new_user


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_superadmin)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Protección del último Super Admin
    if target_user.role == "superadmin":
        active_superadmins = db.query(User).filter(
            User.role == "superadmin",
            User.is_active == True
        ).count()

        # Si se intenta desactivar o cambiar de rol al único superadmin activo
        is_deactivating = body.is_active is False
        is_changing_role = body.role is not None and body.role not in ["superadmin", "admin"]
        
        if active_superadmins <= 1 and (is_deactivating or is_changing_role):
            raise HTTPException(
                status_code=400,
                detail="No se puede desactivar o cambiar el rol del último Super Admin del sistema"
            )

    changes = body.model_dump(exclude_none=True)
    if "password" in changes and changes["password"]:
        target_user.hashed_password = hash_password(changes["password"])
        del changes["password"]
    
    if "role" in changes:
        target_user.role = "superadmin" if changes["role"] in ["superadmin", "admin"] else "operator"
        del changes["role"]

    for k, v in changes.items():
        setattr(target_user, k, v)

    db.commit()
    db.refresh(target_user)

    log_audit_action(
        db,
        username=admin.username,
        action="UPDATE_USER",
        resource_type="user",
        resource_id=str(target_user.id),
        details={"updated_fields": list(changes.keys())}
    )

    return target_user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_superadmin)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Protección del último Super Admin
    if target_user.role == "superadmin":
        active_superadmins = db.query(User).filter(
            User.role == "superadmin",
            User.is_active == True
        ).count()
        if active_superadmins <= 1:
            raise HTTPException(
                status_code=400,
                detail="No se puede eliminar al último Super Admin del sistema"
            )

    username_deleted = target_user.username
    db.delete(target_user)
    db.commit()

    log_audit_action(
        db,
        username=admin.username,
        action="DELETE_USER",
        resource_type="user",
        resource_id=str(user_id),
        details={"username": username_deleted}
    )
