from typing import Dict, Any, List, Tuple
from app.services.detector_service import is_description_row

# Definición conceptual de firmas esperadas para reportes Botmaker (Español e Inglés)
BOTMAKER_EXPECTED_CLUSTERS = {
    "users": [
        ["conversation", "conversación", "conversacion", "link", "id sesión", "id sesion"],
        ["date", "fecha", "fecha sesión", "fecha sesion"],
        ["session", "sesión", "sesion", "id sesión", "id sesion"],
        ["channel", "canal", "id canal"],
        ["contact", "contacto", "user", "usuario", "número", "numero", "id contacto/número", "id contacto/numero"],
        ["agent", "agente", "habló el agente", "hablo el agente", "nombre agente"],
        ["messages", "mensajes", "mensajes usuario", "mensajes bot", "mensajes agente"]
    ],
    "operators_debug": [
        ["session", "sesión", "sesion", "id sesión", "id sesion"],
        ["user", "usuario", "id usuario"],
        ["start", "inicio", "fecha/tiempo inicio sesión", "fecha/tiempo inicio sesion"],
        ["agent", "agente", "nombre agente"],
        ["queue", "cola"],
        ["typification", "tipificación", "tipificacion"]
    ],
    "session_causes": [
        ["user", "usuario", "contact", "contacto", "id usuario", "id contacto/número", "id contacto/numero"],
        ["channel", "canal", "id canal"],
        ["template", "plantilla", "notificación", "notificacion", "nombre plantilla/notificación", "nombre plantilla/notificacion"],
        ["sent", "enviado"],
        ["delivered", "entregado"]
    ]
}
# Soporte de alias para retrocompatibilidad
BOTMAKER_EXPECTED_CLUSTERS["operatorsSessionsDebug"] = BOTMAKER_EXPECTED_CLUSTERS["operators_debug"]
BOTMAKER_EXPECTED_CLUSTERS["sessionStartingCauses"] = BOTMAKER_EXPECTED_CLUSTERS["session_causes"]

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

    # 3. Validación de Botmaker (Bilingüe Español / Inglés)
    elif source_code == "botmaker":
        clusters = BOTMAKER_EXPECTED_CLUSTERS.get(report_type, [])
        if clusters:
            headers_lower = [h.lower() for h in headers]
            missing_labels = []
            for cluster in clusters:
                found = any(any(syn in h for syn in cluster) for h in headers_lower)
                if not found:
                    missing_labels.append(cluster[0])
            if missing_labels:
                warnings.append({
                    "row": 0,
                    "field": "headers",
                    "message": f"Columnas clave no detectadas en reporte '{report_type}': {', '.join(missing_labels)}",
                    "severity": "WARNING"
                })

    # 4. Validación Fila por Fila (Garantizar NO pérdida silenciosa de datos)
    expected_col_count = len(headers)
    for idx, row in enumerate(all_rows[1:], start=2):
        # Ignorar fila 2 si es encabezado secundario de descripciones
        if idx == 2 and is_description_row(row, headers):
            continue

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
