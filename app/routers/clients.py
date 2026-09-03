from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Client, KPIConfig, User
from app.schemas import ClientCreate, ClientUpdate, ClientOut
from app.dependencies import require_superadmin, get_current_user
from app.audit import log_audit_action

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("/", response_model=List[ClientOut])
def list_clients(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Client).order_by(Client.created_at.desc()).all()


@router.post("/", response_model=ClientOut, status_code=201)
def create_client(
    body: ClientCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_superadmin)
):
    client = Client(**body.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)

    # Crear KPIConfigs por defecto basados en kpi_modules
    mods = client.kpi_modules or ["chat_sales", "appointments", "calls", "quality_kidoz"]
    for mod in mods:
        db.add(KPIConfig(
            client_id=client.id,
            kpi_code=mod,
            kpi_name=mod.replace("_", " ").title(),
            source_code="manual"
        ))
    db.commit()

    log_audit_action(
        db,
        username=admin.username,
        action="CREATE_CLIENT",
        resource_type="client",
        resource_id=str(client.id),
        details={"name": client.name, "kpi_modules": client.kpi_modules}
    )

    return client


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


@router.put("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    body: ClientUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_superadmin)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    changes = body.model_dump(exclude_none=True)
    for k, v in changes.items():
        setattr(client, k, v)
    
    db.commit()
    db.refresh(client)

    log_audit_action(
        db,
        username=admin.username,
        action="UPDATE_CLIENT",
        resource_type="client",
        resource_id=str(client.id),
        details=changes
    )

    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_superadmin)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    client_name = client.name
    db.delete(client)
    db.commit()

    log_audit_action(
        db,
        username=admin.username,
        action="DELETE_CLIENT",
        resource_type="client",
        resource_id=str(client_id),
        details={"name": client_name}
    )

