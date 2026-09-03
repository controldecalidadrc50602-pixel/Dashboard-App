from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Client, AnalysisInsight, KPIResult, KPIConfig, ReportImport
from app.schemas import AnalysisInsightOut
from app.dependencies import get_current_user, get_username
from app.audit import log_audit_action

from app.services.analysis_engine.analysis_service import run_rc506_analysis
from app.services.analysis_engine.rules_registry import RC506RulesRegistry

router = APIRouter(prefix="/api/admin/analysis", tags=["analysis"])


@router.post("/run", response_model=List[AnalysisInsightOut])
def run_analysis_endpoint(
    client_id: int,
    period: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_user)
):
    """Ejecuta el Motor de Análisis Determinístico RC506 para un cliente y período."""
    try:
        insights = run_rc506_analysis(db, client_id, period)
        log_audit_action(
            db,
            username=get_username(admin),
            action="RUN_RC506_ANALYSIS",
            resource_type="analysis_insight",
            details={"client_id": client_id, "period": period, "insights_generated": len(insights)},
            ip_address=request.client.host if request.client else None
        )
        return insights
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/clients/{client_id}/insights", response_model=List[AnalysisInsightOut])
def get_client_insights(
    client_id: int,
    period: Optional[str] = None,
    severity: Optional[str] = None,
    analysis_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Consulta los insights determinísticos de un cliente con filtros opcionales."""
    q = db.query(AnalysisInsight).filter(AnalysisInsight.client_id == client_id)

    if period:
        q = q.filter(AnalysisInsight.period == period)
    if severity:
        q = q.filter(AnalysisInsight.severity == severity)
    if analysis_type:
        q = q.filter(AnalysisInsight.analysis_type == analysis_type)

    return q.order_by(AnalysisInsight.created_at.desc()).all()


@router.get("/rules")
def list_analysis_rules(_=Depends(get_current_user)):
    """Lista las reglas declarativas registradas en el Motor de Análisis RC506."""
    return RC506RulesRegistry.list_rules()


@router.get("/insights/{insight_id}/traceability")
def get_insight_traceability(
    insight_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """
    Cadena completa de trazabilidad determinística:
    Insight ➔ KPIResult ➔ KPIConfig ➔ ReportImport ➔ RAW Storage
    """
    insight = db.query(AnalysisInsight).filter(AnalysisInsight.id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight no encontrado")

    client = db.query(Client).filter(Client.id == insight.client_id).first()
    kpi_res = db.query(KPIResult).filter(KPIResult.id == insight.kpi_result_id).first() if insight.kpi_result_id else None
    kpi_cfg = db.query(KPIConfig).filter(KPIConfig.id == insight.kpi_config_id).first() if insight.kpi_config_id else None
    raw_import = db.query(ReportImport).filter(ReportImport.id == kpi_res.import_id).first() if (kpi_res and kpi_res.import_id) else None

    return {
        "insight_id": insight.id,
        "client_name": client.name if client else "Desconocido",
        "period": insight.period,
        "analysis_type": insight.analysis_type,
        "severity": insight.severity,
        "title": insight.title,
        "description": insight.description,
        "rule_id": insight.rule_id,
        "rule_version": insight.rule_version,
        "current_value": insight.current_value,
        "reference_value": insight.reference_value,
        "delta": insight.delta,
        "delta_percent": insight.delta_percent,
        "kpi_info": {
            "kpi_code": kpi_cfg.kpi_code if kpi_cfg else None,
            "kpi_name": kpi_cfg.kpi_name if kpi_cfg else None,
            "formula_used": kpi_res.formula_used if kpi_res else None,
            "input_values": kpi_res.input_values if kpi_res else {}
        },
        "raw_import_info": {
            "import_id": raw_import.id if raw_import else None,
            "original_filename": raw_import.original_filename if raw_import else None,
            "file_hash": raw_import.file_hash if raw_import else None,
            "storage_path": raw_import.storage_path if raw_import else None
        },
        "created_at": insight.created_at
    }
