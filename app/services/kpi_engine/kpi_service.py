from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import Client, KPIConfig, KPIResult, ReportImport, NormalizedRecord
from app.services.kpi_engine.formula_evaluator import FormulaEvaluator
from app.services.normalizer.metrics_calculator_service import calculate_base_metrics

def create_kpi_config(db: Session, client_id: int, data: Dict[str, Any]) -> KPIConfig:
    """Crea una nueva configuración de KPI para un cliente."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError("Cliente no encontrado")

    config = KPIConfig(
        client_id=client_id,
        kpi_code=data.get("kpi_code") or data.get("identifier"),
        kpi_name=data.get("kpi_name") or data.get("name"),
        description=data.get("description"),
        source_code=data.get("source_code") or data.get("source"),
        report_type=data.get("report_type"),
        target_value=data.get("target_value") if data.get("target_value") is not None else data.get("target"),
        formula_type=data.get("formula_type", "ratio"),
        formula_expression=data.get("formula_expression", "a / b * 100"),
        input_metrics=data.get("input_metrics", []),
        direction=data.get("direction", "higher_is_better"),
        unit=data.get("unit", "percentage"),
        period_frequency=data.get("period_frequency", "monthly"),
        thresholds=data.get("thresholds", {}),
        is_active=data.get("is_active", True),
        version=data.get("version", "v1.0")
    )

    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_kpi_config(db: Session, kpi_config_id: int, data: Dict[str, Any]) -> KPIConfig:
    """Actualiza una configuración existente de KPI."""
    config = db.query(KPIConfig).filter(KPIConfig.id == kpi_config_id).first()
    if not config:
        raise ValueError("Configuración de KPI no encontrada")

    for key, val in data.items():
        if hasattr(config, key) and val is not None:
            setattr(config, key, val)

    db.commit()
    db.refresh(config)
    return config


def calculate_kpis_for_client_period(
    db: Session,
    client_id: int,
    period: str
) -> List[KPIResult]:
    """
    Ejecuta el motor de cálculo determinista para todos los KPIs activos del cliente en el período indicado.
    Preserva el histórico en la tabla `kpi_results` con trazabilidad completa.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError("Cliente no encontrado")

    configs = db.query(KPIConfig).filter(
        KPIConfig.client_id == client_id,
        KPIConfig.is_active == True
    ).all()

    # Buscar importaciones del cliente en el período
    imports = db.query(ReportImport).filter(
        ReportImport.client_id == client_id,
        ReportImport.period == period,
        ReportImport.status.in_(["VALID", "VALID_WITH_WARNINGS", "PROCESSED", "PROCESSED_WITH_WARNINGS"])
    ).all()

    results = []

    for cfg in configs:
        # Filtrar importación relevante para este KPI
        matching_import = None
        if cfg.source_code:
            matching_import = next((i for i in imports if i.source_code == cfg.source_code), None)
        if not matching_import and imports:
            matching_import = imports[0]

        input_vals: Dict[str, Optional[float]] = {}
        traceability_info = {
            "kpi_config_id": cfg.id,
            "kpi_code": cfg.kpi_code,
            "version": cfg.version,
            "formula_type": cfg.formula_type,
            "formula_expression": cfg.formula_expression,
            "import_id": matching_import.id if matching_import else None,
            "source_code": cfg.source_code,
            "report_type": cfg.report_type
        }

        # Extraer valores de métricas si existe importación
        if matching_import:
            metrics_summary = calculate_base_metrics(db, matching_import.id)
            b_metrics = metrics_summary.get("metrics", {})

            for input_name in (cfg.input_metrics or []):
                # Buscar en base_metrics o en normalized_data
                val = None
                if input_name in b_metrics:
                    val = b_metrics[input_name].get("value")
                else:
                    # Buscar en los registros normalizados directos
                    records = db.query(NormalizedRecord).filter(
                        NormalizedRecord.import_id == matching_import.id
                    ).all()
                    
                    if input_name in ["answered", "contestadas"]:
                        val = sum(1 for r in records if r.agent or (r.is_abandoned is False))
                    elif input_name in ["total", "totales"]:
                        val = len(records)
                    elif input_name in ["abandoned", "abandonadas"]:
                        val = sum(1 for r in records if r.is_abandoned is True)
                    elif records:
                        # Extraer de raw_data o normalized_data del primer registro
                        sample_row = records[0].normalized_data or records[0].raw_data
                        val = sample_row.get(input_name)

                input_vals[input_name] = float(val) if val is not None else None

        # Evaluar fórmula
        computed_val, err_msg = FormulaEvaluator.evaluate(
            cfg.formula_type,
            input_vals
        )

        status, status_color = FormulaEvaluator.determine_status(
            computed_val,
            cfg.target_value,
            cfg.direction,
            cfg.thresholds
        )

        if err_msg:
            traceability_info["evaluation_note"] = err_msg

        # Upsert resultado en kpi_results
        existing_result = db.query(KPIResult).filter(
            KPIResult.client_id == client_id,
            KPIResult.kpi_config_id == cfg.id,
            KPIResult.period == period
        ).first()

        if existing_result:
            existing_result.value = computed_val
            existing_result.target_value = cfg.target_value
            existing_result.status = status
            existing_result.status_color = status_color
            existing_result.formula_used = f"{cfg.formula_type}: {cfg.formula_expression}"
            existing_result.input_values = input_vals
            existing_result.traceability_info = traceability_info
            existing_result.import_id = matching_import.id if matching_import else None
            res_obj = existing_result
        else:
            res_obj = KPIResult(
                client_id=client_id,
                kpi_config_id=cfg.id,
                import_id=matching_import.id if matching_import else None,
                period=period,
                kpi_code=cfg.kpi_code,
                source_code=cfg.source_code or "generic",
                value=computed_val,
                target_value=cfg.target_value,
                status=status,
                status_color=status_color,
                formula_used=f"{cfg.formula_type}: {cfg.formula_expression}",
                input_values=input_vals,
                traceability_info=traceability_info
            )
            db.add(res_obj)

        db.commit()
        db.refresh(res_obj)
        results.append(res_obj)

    return results
