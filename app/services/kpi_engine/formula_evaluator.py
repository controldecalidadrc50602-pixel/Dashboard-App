from typing import Dict, Any, List, Optional, Tuple

class FormulaEvaluator:
    """
    Motor determinista de cálculo de fórmulas y reglas sin eval().
    Evalúa expresiones algebraicas estructuradas de forma segura y explicable.
    """

    ALLOWED_FORMULA_TYPES = {"ratio", "difference", "percentage_gap", "direct", "sum", "average"}

    @classmethod
    def evaluate(
        cls,
        formula_type: str,
        input_values: Dict[str, Optional[float]],
        scale: float = 100.0
    ) -> Tuple[Optional[float], Optional[str]]:
        """
        Calcula el valor numérico de la fórmula según los valores de entrada.
        Retorna (resultado_float, mensaje_error_si_hubo).
        """
        f_type = (formula_type or "ratio").lower()

        if f_type not in cls.ALLOWED_FORMULA_TYPES:
            return None, f"Tipo de fórmula no soportado: '{formula_type}'"

        # Extraer valores numéricos ordenados de la clave del diccionario
        vals = list(input_values.values())

        if not vals or any(v is None for v in vals):
            return None, "Datos de entrada insuficientes o nulos"

        try:
            if f_type == "direct":
                return float(vals[0]), None

            elif f_type == "ratio":
                if len(vals) < 2:
                    return None, "Fórmula 'ratio' requiere al menos 2 métricas de entrada"
                denom = vals[1]
                if denom == 0:
                    return None, "División por cero en cálculo de ratio"
                return round((vals[0] / denom) * scale, 4), None

            elif f_type == "difference":
                if len(vals) < 2:
                    return None, "Fórmula 'difference' requiere 2 métricas"
                return round(vals[0] - vals[1], 4), None

            elif f_type == "percentage_gap":
                if len(vals) < 2:
                    return None, "Fórmula 'percentage_gap' requiere 2 métricas"
                target_val = vals[1]
                if target_val == 0:
                    return None, "División por cero en gap porcentual"
                return round(((vals[0] - target_val) / target_val) * 100.0, 4), None

            elif f_type == "sum":
                return round(sum(vals), 4), None

            elif f_type == "average":
                return round(sum(vals) / len(vals), 4), None

        except (ZeroDivisionError, ValueError, TypeError) as e:
            return None, f"Error durante la evaluación: {str(e)}"

        return None, "No se pudo evaluar la fórmula"

    @classmethod
    def determine_status(
        cls,
        value: Optional[float],
        target_value: Optional[float],
        direction: str = "higher_is_better",
        thresholds: Optional[Dict[str, float]] = None
    ) -> Tuple[str, str]:
        """
        Determina el estado del KPI y su color asociado (semáforo).
        Retorna (status, color).
        
        Estados:
        - NO_DATA / NOT_AVAILABLE
        - NO_TARGET (si target es None)
        - ON_TARGET / ABOVE_TARGET / BELOW_TARGET
        """
        if value is None:
            return "NOT_AVAILABLE", "gray"

        if target_value is None:
            return "NO_TARGET", "gray"

        dir_clean = (direction or "higher_is_better").lower()
        thresh = thresholds or {}

        warning_th = thresh.get("warning")
        danger_th = thresh.get("danger")

        if dir_clean == "higher_is_better":
            if value >= target_value:
                return "ON_TARGET", "green"
            elif warning_th is not None and value >= warning_th:
                return "BELOW_TARGET", "yellow"
            else:
                return "BELOW_TARGET", "red"

        elif dir_clean == "lower_is_better":
            if value <= target_value:
                return "ON_TARGET", "green"
            elif warning_th is not None and value <= warning_th:
                return "ABOVE_TARGET", "yellow"
            else:
                return "ABOVE_TARGET", "red"

        elif dir_clean == "range":
            min_v = thresh.get("min", target_value * 0.9)
            max_v = thresh.get("max", target_value * 1.1)
            if min_v <= value <= max_v:
                return "ON_TARGET", "green"
            else:
                return "OUT_OF_RANGE", "red"

        return "ON_TARGET" if value >= target_value else "BELOW_TARGET", "gray"
