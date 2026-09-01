from typing import Dict, Any, List, Tuple

# Definición conceptual de firmas esperadas para reportes Botmaker
BOTMAKER_EXPECTED_HEADERS = {
    "users": ["conversation", "date", "time", "session", "channel", "contact", "agent", "messages"],
    "operatorsSessionsDebug": ["session", "user", "start", "end", "agent", "queue", "typification", "wait"],
    "sessionStartingCauses": ["user", "contact", "channel", "template", "sent", "delivered", "read"]
}

# Definición de reportes Yeastar (Marcados como NO VERIFICADO — REQUIERE ARCHIVO DE MUESTRA)
YEASTAR_REPORT_TYPES = ["Extension", "Call Center", "Call Activity", "AI Reports"]


def validate_import_structure(
    source_code: str,
    report_type: str,
    metadata_info: Dict[str, Any],
    all_rows: List[List[str]]
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Valida la estructura, encabezados y contenido fila por fila del archivo.
    Garantiza que NINGUNA fila sea eliminada silenciosamente.
    Retorna (status, warnings_list, errors_list).
    """
    warnings: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    headers = metadata_info.get("headers", [])
    total_rows = metadata_info.get("total_rows", 0)

    # 1. Validar archivo vacío
    if total_rows == 0 and not headers:
        errors.append({
            "row": 0,
            "field": "file",
            "message": "El archivo se encuentra completamente vacío o no posee registros.",
            "severity": "ERROR"
        })
        return "INVALID", warnings, errors

    # 2. Validación de Yeastar (Requiere muestra real)
    if source_code == "yeastar":
        warnings.append({
            "row": 0,
            "field": "schema",
            "message": "Estructura Yeastar: NO VERIFICADO — REQUIERE ARCHIVO DE MUESTRA para validación completa de columnas.",
            "severity": "WARNING"
        })

    # 3. Validación de Botmaker
    elif source_code == "botmaker":
        expected_keys = BOTMAKER_EXPECTED_HEADERS.get(report_type, [])
        if expected_keys:
            headers_lower = [h.lower() for h in headers]
            missing_keys = [k for k in expected_keys if not any(k in h for h in headers_lower)]
            if missing_keys:
                warnings.append({
                    "row": 0,
                    "field": "headers",
                    "message": f"Columnas clave omitidas o diferentes en reporte '{report_type}': {', '.join(missing_keys)}",
                    "severity": "WARNING"
                })

    # 4. Validación Fila por Fila (Garantizar NO pérdida silenciosa de datos)
    expected_col_count = len(headers)
    for idx, row in enumerate(all_rows[1:], start=2):
        if len(row) != expected_col_count:
            warnings.append({
                "row": idx,
                "field": "column_count",
                "message": f"Discrepancia en número de columnas (esperadas {expected_col_count}, encontradas {len(row)}).",
                "severity": "WARNING"
            })
        
        # Validar campos vacíos sospechosos
        blank_fields = [i for i, cell in enumerate(row) if not cell.strip()]
        if len(blank_fields) > (expected_col_count / 2):
            warnings.append({
                "row": idx,
                "field": "data_integrity",
                "message": "Más del 50% de los campos en esta fila se encuentran vacíos.",
                "severity": "WARNING"
            })

    # Determinar estado final
    has_errors = any(e.get("severity") == "ERROR" for e in errors)
    has_warnings = len(warnings) > 0

    if has_errors:
        status = "INVALID"
    elif has_warnings:
        status = "VALID_WITH_WARNINGS"
    else:
        status = "VALID"

    return status, warnings, errors
