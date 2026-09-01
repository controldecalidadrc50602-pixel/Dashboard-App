from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import Client, MonthlyReport, AuditLog, KPIConfig
from app.schemas import (
    DashboardGlobalResponse, GlobalSummaryOut, ClientStatusOut,
    GlobalMetricsOut, PreliminaryAlertOut, AuditLogOut
)
from app.routers.auth import get_current_admin
from app.audit import log_audit_action

router = APIRouter(prefix="/api/admin", tags=["dashboard-global"])

MONTH_NAMES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
               "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


@router.get("/dashboard-global", response_model=DashboardGlobalResponse)
def get_dashboard_global(
    request: Request,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    # Registrar auditoría de visualización del dashboard global
    log_audit_action(
        db,
        username=admin.get("sub", "admin"),
        action="VIEW_DASHBOARD_GLOBAL",
        resource_type="dashboard",
        resource_id="global",
        ip_address=request.client.host if request.client else None
    )

    clients = db.query(Client).all()
    all_reports = db.query(MonthlyReport).all()

    # Determinar el último período global registrado en la base de datos
    latest_global_year = None
    latest_global_month = None

    if all_reports:
        latest_rep = max(all_reports, key=lambda r: (r.year, r.month))
        latest_global_year = latest_rep.year
        latest_global_month = latest_rep.month

    period_label = (
        f"{MONTH_NAMES[latest_global_month]} {latest_global_year}"
        if latest_global_year and latest_global_month
        else "Sin datos"
    )

    latest_period_info = {
        "year": latest_global_year,
        "month": latest_global_month,
        "period_label": period_label
    }

    # Procesar estado por cliente
    active_clients = [c for c in clients if c.is_active]
    client_statuses = []
    clients_with_data_count = 0
    updated_reports_count = 0
    pending_reports_count = 0

    preliminary_alerts = []

    # Métricas agregadas globales
    total_chats = 0
    total_calls = 0
    total_leads = 0
    total_sales = 0
    csat_values = []

    for client in clients:
        c_reports = [r for r in all_reports if r.client_id == client.id]
        has_data = len(c_reports) > 0

        # Contar KPIs configurados
        kpi_configs_count = db.query(KPIConfig).filter(
            KPIConfig.client_id == client.id,
            KPIConfig.is_active == True
        ).count()

        if kpi_configs_count == 0 and client.kpi_modules:
            kpi_configs_count = len(client.kpi_modules)

        latest_c_report = max(c_reports, key=lambda r: (r.year, r.month)) if c_reports else None

        if not client.is_active:
            status = "inactivo"
            status_label = "Inactivo"
        elif not has_data and kpi_configs_count == 0:
            status = "requiere_configuracion"
            status_label = "Requiere Configuración"
            preliminary_alerts.append(PreliminaryAlertOut(
                id=f"alert-cfg-{client.id}",
                type="warning",
                title="Configuración pendiente",
                message=f"El cliente '{client.name}' está activo pero no posee KPIs ni reportes configurados.",
                client_id=client.id,
                client_name=client.name
            ))
        elif latest_global_year and latest_global_month and latest_c_report and \
             (latest_c_report.year == latest_global_year and latest_c_report.month == latest_global_month):
            status = "actualizado"
            status_label = "Actualizado"
            updated_reports_count += 1
        elif has_data:
            status = "pendiente"
            status_label = "Pendiente"
            pending_reports_count += 1
            preliminary_alerts.append(PreliminaryAlertOut(
                id=f"alert-pending-{client.id}",
                type="info",
                title="Reporte pendiente",
                message=f"El cliente '{client.name}' requiere actualizar su reporte para el período {period_label}.",
                client_id=client.id,
                client_name=client.name
            ))
        else:
            status = "pendiente"
            status_label = "Pendiente"
            pending_reports_count += 1

        if has_data and client.is_active:
            clients_with_data_count += 1

        # Sumar métricas para la vista global (solo reportes del cliente)
        for r in c_reports:
            total_chats += (r.chats or 0)
            total_calls += (r.total_calls or 0)
            total_leads += (r.leads or 0)
            total_sales += (r.sales or 0)
            if r.csat and r.csat > 0:
                csat_values.append(r.csat)

        period_str = (
            f"{MONTH_NAMES[latest_c_report.month]} {latest_c_report.year}"
            if latest_c_report else "Sin reportes"
        )

        client_statuses.append(ClientStatusOut(
            id=client.id,
            name=client.name,
            color=client.color or "#009688",
            logo_text=client.logo_text or "RC",
            is_active=client.is_active,
            period=period_str,
            status=status,
            status_label=status_label,
            kpis_count=kpi_configs_count,
            has_data=has_data,
            total_reports=len(c_reports),
            latest_report_year=latest_c_report.year if latest_c_report else None,
            latest_report_month=latest_c_report.month if latest_c_report else None,
            latest_report_month_name=MONTH_NAMES[latest_c_report.month] if latest_c_report else None
        ))

    avg_csat = round(sum(csat_values) / len(csat_values), 2) if csat_values else 0.0

    summary = GlobalSummaryOut(
        total_active_clients=len(active_clients),
        clients_with_data=clients_with_data_count,
        updated_reports_count=updated_reports_count,
        pending_reports_count=pending_reports_count,
        latest_period=latest_period_info
    )

    global_metrics = GlobalMetricsOut(
        total_chats=total_chats,
        total_calls=total_calls,
        total_leads=total_leads,
        total_sales=total_sales,
        avg_csat=avg_csat
    )

    # Actividad reciente desde AuditLog
    recent_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
    recent_activity = [AuditLogOut.model_validate(l) for l in recent_logs]

    return DashboardGlobalResponse(
        summary=summary,
        client_statuses=client_statuses,
        global_metrics=global_metrics,
        preliminary_alerts=preliminary_alerts,
        recent_activity=recent_activity
    )
