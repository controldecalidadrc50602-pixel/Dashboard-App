from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Client, KPIConfig, KPIResult, AnalysisInsight, NormalizedRecord, ReportImport
from app.services.analysis_engine.rules_registry import RC506RulesRegistry


def get_previous_period_str(period: str) -> Optional[str]:
    """Calcula el período YYYY-MM inmediatamente anterior."""
    try:
        parts = period.split("-")
        year, month = int(parts[0]), int(parts[1])
        if month == 1:
            return f"{year - 1}-12"
        else:
            return f"{year}-{month - 1:02d}"
    except Exception:
        return None


def run_rc506_analysis(db: Session, client_id: int, period: str) -> List[AnalysisInsight]:
    """
    Ejecuta el Motor de Análisis Determinístico RC506.
    Lee los resultados KPI calculados (Fase 04) y genera observaciones e insights explicables.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError("Cliente no encontrado")

    # Limpiar insights previos del cliente y período para garantizar idempotencia
    db.query(AnalysisInsight).filter(
        AnalysisInsight.client_id == client_id,
        AnalysisInsight.period == period
    ).delete(synchronize_session=False)
    db.commit()

    # Obtener resultados de KPIs del período
    kpi_results = db.query(KPIResult).filter(
        KPIResult.client_id == client_id,
        KPIResult.period == period
    ).all()

    insights = []
    prev_period = get_previous_period_str(period)

    for res in kpi_results:
        cfg = db.query(KPIConfig).filter(KPIConfig.id == res.kpi_config_id).first()
        kpi_name = cfg.kpi_name if cfg else res.kpi_code
        direction = cfg.direction if cfg else "higher_is_better"

        # ── 1. TARGET COMPLIANCE ANALYSIS ──
        if res.status in ["BELOW_TARGET", "ABOVE_TARGET"]:
            gap = abs((res.value or 0) - (res.target_value or 0))
            gap_pct = (gap / res.target_value * 100.0) if res.target_value else 0
            severity = "CRITICAL" if gap_pct > 15.0 else "WARNING"

            insight = AnalysisInsight(
                client_id=client_id,
                period=period,
                analysis_type="TARGET_COMPLIANCE",
                severity=severity,
                title=f"Desviación de Meta en {kpi_name}",
                description=f"El indicador {kpi_name} ({res.kpi_code}) registró {res.value}, ubicándose fuera de la meta configurada de {res.target_value} (diferencial de {round(gap, 2)}).",
                kpi_config_id=res.kpi_config_id,
                kpi_result_id=res.id,
                current_value=res.value,
                reference_value=res.target_value,
                delta=round(gap, 4),
                delta_percent=round(gap_pct, 4) if gap_pct else None,
                rule_id="rule_target_compliance_v1",
                rule_version="v1.0",
                source_references=res.traceability_info or {}
            )
            db.add(insight)
            insights.append(insight)

        elif res.status == "ON_TARGET":
            insight = AnalysisInsight(
                client_id=client_id,
                period=period,
                analysis_type="TARGET_COMPLIANCE",
                severity="POSITIVE",
                title=f"Meta Alcanzada en {kpi_name}",
                description=f"El indicador {kpi_name} ({res.kpi_code}) alcanzó un desempeño de {res.value}, cumpliendo la meta esperada de {res.target_value}.",
                kpi_config_id=res.kpi_config_id,
                kpi_result_id=res.id,
                current_value=res.value,
                reference_value=res.target_value,
                delta=0.0,
                delta_percent=0.0,
                rule_id="rule_target_compliance_v1",
                rule_version="v1.0",
                source_references=res.traceability_info or {}
            )
            db.add(insight)
            insights.append(insight)

        elif res.status == "NO_TARGET":
            insight = AnalysisInsight(
                client_id=client_id,
                period=period,
                analysis_type="TARGET_COMPLIANCE",
                severity="INFO",
                title=f"Evaluación sin Meta en {kpi_name}",
                description=f"El indicador {kpi_name} ({res.kpi_code}) registró un valor de {res.value}. No posee meta asignada (NO_TARGET).",
                kpi_config_id=res.kpi_config_id,
                kpi_result_id=res.id,
                current_value=res.value,
                reference_value=None,
                rule_id="rule_target_compliance_v1",
                rule_version="v1.0",
                source_references=res.traceability_info or {}
            )
            db.add(insight)
            insights.append(insight)

        elif res.status == "NOT_AVAILABLE":
            insight = AnalysisInsight(
                client_id=client_id,
                period=period,
                analysis_type="DATA_QUALITY",
                severity="NOT_AVAILABLE",
                title=f"Datos Insuficientes para {kpi_name}",
                description=f"No existen datos o métricas suficientes en la fuente para evaluar {kpi_name} en el período {period}.",
                kpi_config_id=res.kpi_config_id,
                kpi_result_id=res.id,
                current_value=None,
                reference_value=res.target_value,
                rule_id="rule_data_quality_v1",
                rule_version="v1.0",
                source_references=res.traceability_info or {}
            )
            db.add(insight)
            insights.append(insight)

        # ── 2. PERIOD OVER PERIOD (MoM) ANALYSIS ──
        if prev_period and res.value is not None:
            prev_res = db.query(KPIResult).filter(
                KPIResult.client_id == client_id,
                KPIResult.kpi_config_id == res.kpi_config_id,
                KPIResult.period == prev_period
            ).first()

            if prev_res and prev_res.value is not None:
                delta = res.value - prev_res.value
                delta_pct = (delta / prev_res.value * 100.0) if prev_res.value != 0 else None

                is_positive = (delta > 0 and direction == "higher_is_better") or (delta < 0 and direction == "lower_is_better")
                severity = "POSITIVE" if is_positive else ("WARNING" if abs(delta) > 5 else "INFO")
                direction_txt = "mejora" if is_positive else "variación"

                insight = AnalysisInsight(
                    client_id=client_id,
                    period=period,
                    analysis_type="PERIOD_OVER_PERIOD",
                    severity=severity,
                    title=f"Comparativo MoM en {kpi_name} ({prev_period} vs {period})",
                    description=f"{kpi_name} presentó una {direction_txt} de {round(delta, 2)} unidades ({round(delta_pct, 2)}% respecto a {prev_period}).",
                    kpi_config_id=res.kpi_config_id,
                    kpi_result_id=res.id,
                    current_value=res.value,
                    reference_value=prev_res.value,
                    delta=round(delta, 4),
                    delta_percent=round(delta_pct, 4) if delta_pct is not None else None,
                    rule_id="rule_period_over_period_v1",
                    rule_version="v1.0",
                    source_references={"prev_period": prev_period, "prev_value": prev_res.value}
                )
                db.add(insight)
                insights.append(insight)

        # ── 3. HISTORICAL TREND ANALYSIS (3+ PERIODS) ──
        hist_results = db.query(KPIResult).filter(
            KPIResult.client_id == client_id,
            KPIResult.kpi_config_id == res.kpi_config_id,
            KPIResult.value != None
        ).order_by(KPIResult.period.asc()).all()

        if len(hist_results) >= 3:
            vals = [r.value for r in hist_results[-3:]]
            is_increasing = vals[0] < vals[1] < vals[2]
            is_decreasing = vals[0] > vals[1] > vals[2]

            trend_status = "improving" if (is_increasing and direction == "higher_is_better") else ("declining" if (is_decreasing and direction == "higher_is_better") else "stable")
            severity = "POSITIVE" if trend_status == "improving" else ("WARNING" if trend_status == "declining" else "INFO")

            insight = AnalysisInsight(
                client_id=client_id,
                period=period,
                analysis_type="TREND",
                severity=severity,
                title=f"Tendencia Histórica {trend_status.upper()} en {kpi_name}",
                description=f"Trayectoria evaluada en los últimos 3 períodos: {vals[0]} ➔ {vals[1]} ➔ {vals[2]}. Tendencia determinística: '{trend_status}'.",
                kpi_config_id=res.kpi_config_id,
                kpi_result_id=res.id,
                current_value=res.value,
                reference_value=vals[0],
                rule_id="rule_trend_v1",
                rule_version="v1.0",
                source_references={"periods_evaluated": [r.period for r in hist_results[-3:]], "values": vals}
            )
            db.add(insight)
            insights.append(insight)

    db.commit()
    for ins in insights:
        db.refresh(ins)

    return insights
