from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid
from app.database import get_db
from app.models import PublicView, MonthlyReport, Client
from app.schemas import PublicViewCreate, PublicViewOut
from app.auth import hash_password, verify_password
from app.dependencies import get_current_user

router = APIRouter(tags=["public"])

MONTH_NAMES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
               "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


# ── Admin: gestión de links públicos ───────────────────────────────────────
@router.get("/api/clients/{client_id}/public-views", response_model=List[PublicViewOut])
def list_public_views(client_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    views = db.query(PublicView).filter(PublicView.client_id == client_id).all()
    result = []
    for v in views:
        d = PublicViewOut.model_validate(v)
        d.has_password = bool(v.password_hash)
        result.append(d)
    return result


@router.post("/api/clients/{client_id}/public-views", status_code=201)
def create_public_view(client_id: int, body: PublicViewCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    token = str(uuid.uuid4())
    pw_hash = hash_password(body.password) if body.password else None
    data = body.model_dump(exclude={"password"})
    view = PublicView(client_id=client_id, token=token, password_hash=pw_hash, **data)
    db.add(view)
    db.commit()
    db.refresh(view)
    out = PublicViewOut.model_validate(view)
    out.has_password = bool(view.password_hash)
    return out


@router.put("/api/clients/{client_id}/public-views/{view_id}")
def update_public_view(
    client_id: int, view_id: int, body: PublicViewCreate,
    db: Session = Depends(get_db), _=Depends(get_current_user)
):
    view = db.query(PublicView).filter(PublicView.id == view_id, PublicView.client_id == client_id).first()
    if not view:
        raise HTTPException(status_code=404, detail="Vista pública no encontrada")
    data = body.model_dump(exclude={"password"})
    for k, v in data.items():
        setattr(view, k, v)
    if body.password:
        view.password_hash = hash_password(body.password)
    db.commit()
    db.refresh(view)
    return view


@router.delete("/api/clients/{client_id}/public-views/{view_id}", status_code=204)
def delete_public_view(client_id: int, view_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    view = db.query(PublicView).filter(PublicView.id == view_id, PublicView.client_id == client_id).first()
    if not view:
        raise HTTPException(status_code=404, detail="Vista pública no encontrada")
    db.delete(view)
    db.commit()


# ── Endpoint público: datos para el cliente ────────────────────────────────
@router.get("/api/public/{token}")
def get_public_data(token: str, password: str = None, db: Session = Depends(get_db)):
    view = db.query(PublicView).filter(PublicView.token == token).first()
    if not view or not view.is_active:
        raise HTTPException(status_code=404, detail="Enlace no encontrado o desactivado")
    if view.expires_at and datetime.utcnow() > view.expires_at:
        raise HTTPException(status_code=410, detail="Este enlace ha expirado")
    if view.password_hash:
        if not password or not verify_password(password, view.password_hash):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    # Incrementar contador de vistas
    view.views_count += 1
    db.commit()

    # Obtener cliente
    client = db.query(Client).filter(Client.id == view.client_id).first()

    # Obtener reportes filtrados
    q = db.query(MonthlyReport).filter(MonthlyReport.client_id == view.client_id)
    if view.show_year:
        q = q.filter(MonthlyReport.year == view.show_year)
    if view.show_months_from:
        q = q.filter(MonthlyReport.month >= view.show_months_from)
    if view.show_months_to:
        q = q.filter(MonthlyReport.month <= view.show_months_to)
    reports = q.order_by(MonthlyReport.year, MonthlyReport.month).all()

    reports_data = []
    for r in reports:
        d = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        d["closing_rate"] = round((r.sales / r.leads * 100), 1) if r.leads else 0.0
        d["month_name"] = MONTH_NAMES[r.month] if 1 <= r.month <= 12 else str(r.month)
        reports_data.append(d)

    return {
        "title": view.title,
        "description": view.description,
        "visible_sections": view.visible_sections,
        "client": {"name": client.name, "color": client.color, "logo_text": client.logo_text, "kpi_modules": client.kpi_modules},
        "reports": reports_data,
        "generated_at": datetime.utcnow().isoformat()
    }
