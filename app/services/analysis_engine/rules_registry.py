from typing import Dict, Any, List

class RC506RulesRegistry:
    """
    Catálogo declarativo de reglas de negocio determinísticas RC506.
    Prohíbe estrictamente eval(), exec() y código Python dinámico.
    """

    RULES = [
        {
            "rule_id": "rule_target_compliance_v1",
            "rule_name": "Evaluación de Cumplimiento de Meta",
            "version": "v1.0",
            "analysis_type": "TARGET_COMPLIANCE",
            "description": "Determina si un KPI cumple la meta configurada sin inferencias arbitrarias."
        },
        {
            "rule_id": "rule_period_over_period_v1",
            "rule_name": "Comparación Período contra Período (MoM)",
            "version": "v1.0",
            "analysis_type": "PERIOD_OVER_PERIOD",
            "description": "Compara el resultado del período actual contra el período anterior disponible."
        },
        {
            "rule_id": "rule_trend_v1",
            "rule_name": "Análisis de Tendencia Histórica (3+ Períodos)",
            "version": "v1.0",
            "analysis_type": "TREND",
            "description": "Clasifica la evolución histórica en improving, declining o stable para un mínimo de 3 períodos."
        },
        {
            "rule_id": "rule_variation_threshold_v1",
            "rule_name": "Detección de Variación Significativa",
            "version": "v1.0",
            "analysis_type": "THRESHOLD_VARIATION",
            "description": "Genera alerta cuando la variación porcentual excede el umbral configurado (ej. > 10%)."
        },
        {
            "rule_id": "rule_concentration_v1",
            "rule_name": "Concentración Operacional por Cola/Agente",
            "version": "v1.0",
            "analysis_type": "CONCENTRATION",
            "description": "Identifica colas o agentes que concentran un porcentaje desproporcionado del volumen total."
        },
        {
            "rule_id": "rule_data_quality_v1",
            "rule_name": "Auditoría de Calidad y Suficiencia de Datos",
            "version": "v1.0",
            "analysis_type": "DATA_QUALITY",
            "description": "Verifica si existen datos nulos, ausentes o insuficientes para la evaluación."
        }
    ]

    @classmethod
    def list_rules(cls) -> List[Dict[str, Any]]:
        return cls.RULES

    @classmethod
    def get_rule(cls, rule_id: str) -> Dict[str, Any]:
        return next((r for r in cls.RULES if r["rule_id"] == rule_id), None)
