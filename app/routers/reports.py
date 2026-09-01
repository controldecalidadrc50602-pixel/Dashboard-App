from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import MonthlyReport, Client
from app.schemas import ReportCreate, ReportUpdate, ReportOut
from app.routers.auth import get_current_admin
from app.audit import log_audit_action

router = APIRouter(prefix="/api/clients", tags=["reports"])

MONTH_NAMES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
               "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def _enrich(report: MonthlyReport) -> dict:
    """Agrega campo calculado closing_rate al reporte."""
    d = {c.name: getattr(report, c.name) for c in report.__table__.columns}
    d["closing_rate"] = round((report.sales / report.leads * 100), 1) if report.leads else 0.0
    d["month_name"] = MONTH_NAMES[report.month] if 1 <= report.month <= 12 else str(report.month)
    return d


@router.get("/{client_id}/reports")
def list_reports(
    client_id: int,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    q = db.query(MonthlyReport).filter(MonthlyReport.client_id == client_id)
    if year:
        q = q.filter(MonthlyReport.year == year)
    reports = q.order_by(MonthlyReport.year, MonthlyReport.month).all()
    return [_enrich(r) for r in reports]


@router.post("/{client_id}/reports", status_code=201)
def create_report(
    client_id: int,
    body: ReportCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Verificar que no exista ya ese mes/año
    existing = db.query(MonthlyReport).filter(
        MonthlyReport.client_id == client_id,
        MonthlyReport.year == body.year,
        MonthlyReport.month == body.month
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un reporte para ese mes/año. Use PUT para actualizar.")
    
    report = MonthlyReport(client_id=client_id, **body.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)

    log_audit_action(
        db,
        username=admin.get("sub", "admin"),
        action="CREATE_REPORT",
        resource_type="report",
        resource_id=str(report.id),
        details={"client_id": client_id, "year": report.year, "month": report.month}
    )

    return _enrich(report)


@router.put("/{client_id}/reports/{report_id}")
def update_report(
    client_id: int, report_id: int, body: ReportUpdate,
    db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)
):
    report = db.query(MonthlyReport).filter(
        MonthlyReport.id == report_id,
        MonthlyReport.client_id == client_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    changes = body.model_dump(exclude_none=True)
    for k, v in changes.items():
        setattr(report, k, v)
    
    db.commit()
    db.refresh(report)

    log_audit_action(
        db,
        username=admin.get("sub", "admin"),
        action="UPDATE_REPORT",
        resource_type="report",
        resource_id=str(report_id),
        details={"client_id": client_id, "changes": list(changes.keys())}
    )

    return _enrich(report)


@router.delete("/{client_id}/reports/{report_id}", status_code=204)
def delete_report(
    client_id: int, report_id: int,
    db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)
):
    report = db.query(MonthlyReport).filter(
        MonthlyReport.id == report_id,
        MonthlyReport.client_id == client_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    rep_period = f"{report.year}-{report.month}"
    db.delete(report)
    db.commit()

    log_audit_action(
        db,
        username=admin.get("sub", "admin"),
        action="DELETE_REPORT",
        resource_type="report",
        resource_id=str(report_id),
        details={"client_id": client_id, "period": rep_period}
    )

