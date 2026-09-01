from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Client, KPIConfig, KPIResult
from app.schemas import KPIConfigOut, KPIConfigCreate, KPIConfigUpdate, KPIResultOut
from app.routers.auth import get_current_admin
from app.audit import log_audit_action

from app.services.kpi_engine.kpi_service import (
    create_kpi_config,
    update_kpi_config,
    calculate_kpis_for_client_period
)

router = APIRouter(prefix="/api/admin/kpis", tags=["kpis"])


@router.get("/clients/{client_id}", response_model=List[KPIConfigOut])
def list_client_kpi_configs(
    client_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    """Obtiene la lista de configuraciones KPI de un cliente."""
    configs = db.query(KPIConfig).filter(KPIConfig.client_id == client_id).all()
    return configs


@router.post("/clients/{client_id}", response_model=KPIConfigOut, status_code=201)
def create_client_kpi_config(
    client_id: int,
    data: KPIConfigCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Crea un nuevo KPI dinámico para un cliente."""
    try:
        config = create_kpi_config(db, client_id, data.model_dump())
        log_audit_action(
            db,
            username=admin.get("sub", "admin"),
            action="CREATE_KPI_CONFIG",
            resource_type="kpi_config",
            resource_id=str(config.id),
            details={"client_id": client_id, "kpi_code": config.kpi_code},
            ip_address=request.client.host if request.client else None
        )
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{kpi_config_id}", response_model=KPIConfigOut)
def update_kpi_config_endpoint(
    kpi_config_id: int,
    data: KPIConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Actualiza la configuración o metas de un KPI."""
    try:
        config = update_kpi_config(db, kpi_config_id, data.model_dump(exclude_unset=True))
        log_audit_action(
            db,
            username=admin.get("sub", "admin"),
            action="UPDATE_KPI_CONFIG",
            resource_type="kpi_config",
            resource_id=str(config.id),
            details=data.model_dump(exclude_unset=True),
            ip_address=request.client.host if request.client else None
        )
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{kpi_config_id}")
def toggle_or_delete_kpi_config(
    kpi_config_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Desactiva una configuración de KPI."""
    config = db.query(KPIConfig).filter(KPIConfig.id == kpi_config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="KPI no encontrado")
    config.is_active = False
    db.commit()
    return {"message": "KPI desactivado correctamente", "id": kpi_config_id}


@router.post("/calculate", response_model=List[KPIResultOut])
def calculate_kpis_endpoint(
    client_id: int,
    period: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Ejecuta el cálculo de KPIs dinámicos para un cliente y período."""
    try:
        results = calculate_kpis_for_client_period(db, client_id, period)
        log_audit_action(
            db,
            username=admin.get("sub", "admin"),
            action="CALCULATE_KPIS",
            resource_type="kpi_results",
            details={"client_id": client_id, "period": period, "count": len(results)}
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/results", response_model=List[KPIResultOut])
def get_kpi_results(
    client_id: Optional[int] = None,
    period: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    """Consulta el historial de resultados KPI calculados."""
    q = db.query(KPIResult)
    if client_id:
        q = q.filter(KPIResult.client_id == client_id)
    if period:
        q = q.filter(KPIResult.period == period)

    return q.order_by(KPIResult.calculated_at.desc()).all()


@router.get("/results/{result_id}/traceability")
def get_kpi_result_traceability(
    result_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    """Devuelve la trazabilidad completa del cálculo de un KPI (Configuración, Importación, Fórmulas, Métricas)."""
    res = db.query(KPIResult).filter(KPIResult.id == result_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resultado de KPI no encontrado")

    cfg = db.query(KPIConfig).filter(KPIConfig.id == res.kpi_config_id).first()
    client = db.query(Client).filter(Client.id == res.client_id).first()

    return {
        "result_id": res.id,
        "client_name": client.name if client else "Desconocido",
        "period": res.period,
        "kpi_code": res.kpi_code,
        "kpi_name": cfg.kpi_name if cfg else res.kpi_code,
        "value": res.value,
        "target_value": res.target_value,
        "status": res.status,
        "status_color": res.status_color,
        "formula_used": res.formula_used,
        "input_values": res.input_values,
        "traceability_info": res.traceability_info,
        "calculated_at": res.calculated_at
    }
