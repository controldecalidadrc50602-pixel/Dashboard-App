import csv
import io
import re
import math
import unicodedata
from typing import Dict, Any, List, Tuple, Optional
import openpyxl

from app.services.detector_service import detect_encoding, detect_delimiter, extract_period_from_filename, detect_botmaker_report_type, is_description_row

def _normalize_str(s: str) -> str:
    """Elimina tildes, convierte a minúsculas y remueve espacios sobrantes."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(s))
    ascii_str = nfkd.encode("ASCII", "ignore").decode("utf-8")
    return ascii_str.lower().strip()


def find_header_row(raw_rows: List[List[str]]) -> Tuple[int, List[str], List[List[str]]]:
    """
    Identifica la fila de encabezado real ignorando filas vacías, de guiones '---',
    o leyendas secundarias (como en operatorsSessionsDebug).
    Retorna (header_index, cleaned_headers, data_rows).
    """
    if not raw_rows:
        return 0, [], []

    header_idx = 0
    headers: List[str] = []

    for idx, row in enumerate(raw_rows[:5]):
        row_str = "".join(str(c).strip() for c in row)
        if not row_str or set(row_str) <= {"-", "=", "#", "*"}:
            continue

        # Si es una fila descriptiva/leyenda
        if is_description_row(row, headers):
            continue

        # Evaluar candidato
        clean_row = [str(c).strip() for c in row]
        non_empty = [c for c in clean_row if c]
        if len(non_empty) > len(headers):
            headers = clean_row
            header_idx = idx

    if not headers and raw_rows:
        headers = [str(c).strip() for c in raw_rows[0]]
        header_idx = 0

    data_rows = []
    for idx, row in enumerate(raw_rows[header_idx + 1:], start=header_idx + 1):
        row_str = "".join(str(c).strip() for c in row)
        if not row_str or set(row_str) <= {"-", "=", "#", "*"}:
            continue
        if idx == header_idx + 1 and is_description_row(row, headers):
            continue
        data_rows.append([str(c).strip() for c in row])

    return header_idx, headers, data_rows


def discover_schema(headers: List[str], rows: List[List[str]]) -> Dict[str, Dict[str, Any]]:
    """
    Descubre automáticamente el tipo de dato de cada columna:
    - categorical (pocos valores únicos / baja variabilidad)
    - numeric (valores parseables a float)
    - temporal (fechas / timestamps)
    - id (UUIDs, links, cadenas únicas largas)
    - text (texto libre)
    """
    schema: Dict[str, Dict[str, Any]] = {}
    total_rows = len(rows)

    date_regex = re.compile(
        r'^(\d{4}[\.\-/]\d{1,2}[\.\-/]\d{1,2}|\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{2,4}|\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:?\d{0,2})'
    )

    for col_idx, col_name in enumerate(headers):
        clean_name = col_name if col_name else f"col_{col_idx}"
        values = []
        for r in rows:
            if col_idx < len(r) and r[col_idx] != "":
                values.append(r[col_idx])

        null_count = total_rows - len(values)
        if not values:
            schema[clean_name] = {
                "index": col_idx,
                "type": "text",
                "null_count": null_count,
                "unique_count": 0,
                "sample_values": []
            }
            continue

        unique_vals = set(values)
        unique_count = len(unique_vals)
        unique_ratio = unique_count / len(values)

        # 1. Chequeo Temporal
        temporal_matches = sum(1 for v in values if date_regex.match(v))
        if temporal_matches / len(values) >= 0.5:
            schema[clean_name] = {
                "index": col_idx,
                "type": "temporal",
                "null_count": null_count,
                "unique_count": unique_count,
                "sample_values": list(unique_vals)[:5]
            }
            continue

        # 2. Chequeo Numérico
        numeric_parsed = []
        for v in values:
            v_clean = v.replace("%", "").replace("$", "").replace(" ", "").replace(",", ".")
            try:
                numeric_parsed.append(float(v_clean))
            except ValueError:
                pass

        if len(numeric_parsed) / len(values) >= 0.7:
            mean_val = sum(numeric_parsed) / len(numeric_parsed) if numeric_parsed else 0.0
            variance = sum((x - mean_val) ** 2 for x in numeric_parsed) / len(numeric_parsed) if numeric_parsed else 0.0
            std_val = math.sqrt(variance)

            schema[clean_name] = {
                "index": col_idx,
                "type": "numeric",
                "null_count": null_count,
                "unique_count": unique_count,
                "sample_values": numeric_parsed[:5],
                "stats": {
                    "mean": round(mean_val, 2),
                    "std": round(std_val, 2),
                    "min": round(min(numeric_parsed), 2) if numeric_parsed else 0,
                    "max": round(max(numeric_parsed), 2) if numeric_parsed else 0
                }
            }
            continue

        # 3. Chequeo ID (UUIDs, URLs, IDs únicos largos)
        sample_str = values[0]
        if unique_ratio >= 0.7 and (len(sample_str) > 15 or "http" in sample_str or "-" in sample_str and len(sample_str) > 10):
            schema[clean_name] = {
                "index": col_idx,
                "type": "id",
                "null_count": null_count,
                "unique_count": unique_count,
                "sample_values": list(unique_vals)[:5]
            }
            continue

        # 4. Chequeo Categórico
        if unique_count <= min(25, max(5, total_rows * 0.3)) or unique_ratio < 0.3:
            schema[clean_name] = {
                "index": col_idx,
                "type": "categorical",
                "null_count": null_count,
                "unique_count": unique_count,
                "categories": list(unique_vals)[:10],
                "sample_values": list(unique_vals)[:5]
            }
            continue

        # 5. Texto por defecto
        schema[clean_name] = {
            "index": col_idx,
            "type": "text",
            "null_count": null_count,
            "unique_count": unique_count,
            "sample_values": list(unique_vals)[:5]
        }

    return schema


def extract_metrics(headers: List[str], rows: List[List[str]], schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Busca semánticamente columnas clave por palabras clave normalizadas e idioma agnóstico.
    Extrae métricas operativas (agentes, mensajes, plantillas, llamadas).
    """
    col_map: Dict[str, int] = {}
    norm_headers = [_normalize_str(h) for h in headers]

    keywords = {
        "agente_hablo": ["hablo el agente", "hablo agente", "agent talked", "agente hablo", "hablo el operador", "hablo operador"],
        "user_messages": ["mensajes usuario", "user messages", "mensajes del usuario", "msg usuario"],
        "bot_messages": ["mensajes bot", "bot messages", "msg bot"],
        "agent_messages": ["mensajes agente", "agent messages", "msg agente", "mensajes operador"],
        "typification": ["tipificacion", "typification", "motivo", "categoria"],
        "template_name": ["nombre plantilla/notificacion", "nombre plantilla", "template name", "plantilla", "notificacion"],
        "template_sent": ["enviado", "sent", "enviadas"],
        "template_not_sent": ["no enviado", "not sent", "fallido"],
        "template_delivered": ["entregado", "delivered", "entregadas"],
        "template_read": ["leida", "read", "leidas"],
        "template_responded": ["respondida", "responded", "respondidas"],
        "total_calls": ["total llamadas", "total calls", "llamadas totales"],
        "answered_calls": ["llamadas contestadas", "answered calls", "contestadas"]
    }

    for metric_key, key_phrases in keywords.items():
        for idx, h in enumerate(norm_headers):
            if metric_key == "template_sent" and "no enviado" in h:
                continue
            if any(phrase in h for phrase in key_phrases):
                col_map[metric_key] = idx
                break

    total_conversations = len(rows)
    conversations_with_agent = 0
    conversations_bot_only = 0

    total_messages_user = 0
    total_messages_bot = 0
    total_messages_agent = 0

    total_templates_sent = 0
    total_templates_delivered = 0
    total_templates_read = 0
    total_templates_responded = 0
    total_templates_not_sent = 0

    total_calls = 0
    answered_calls = 0

    for r in rows:
        # Agente habló
        if "agente_hablo" in col_map:
            idx = col_map["agente_hablo"]
            val = r[idx].lower() if idx < len(r) else ""
            if val in ["1", "true", "si", "yes", "s"]:
                conversations_with_agent += 1
            else:
                conversations_bot_only += 1

        # Mensajes
        if "user_messages" in col_map:
            try: total_messages_user += int(r[col_map["user_messages"]])
            except (ValueError, IndexError): pass
        if "bot_messages" in col_map:
            try: total_messages_bot += int(r[col_map["bot_messages"]])
            except (ValueError, IndexError): pass
        if "agent_messages" in col_map:
            try: total_messages_agent += int(r[col_map["agent_messages"]])
            except (ValueError, IndexError): pass

        # Plantillas
        if "template_sent" in col_map:
            try: total_templates_sent += int(r[col_map["template_sent"]])
            except (ValueError, IndexError): pass
        if "template_delivered" in col_map:
            try: total_templates_delivered += int(r[col_map["template_delivered"]])
            except (ValueError, IndexError): pass
        if "template_read" in col_map:
            try: total_templates_read += int(r[col_map["template_read"]])
            except (ValueError, IndexError): pass
        if "template_responded" in col_map:
            try: total_templates_responded += int(r[col_map["template_responded"]])
            except (ValueError, IndexError): pass
        if "template_not_sent" in col_map:
            try: total_templates_not_sent += int(r[col_map["template_not_sent"]])
            except (ValueError, IndexError): pass

        # Llamadas
        if "total_calls" in col_map:
            try: total_calls += int(r[col_map["total_calls"]])
            except (ValueError, IndexError): pass
        if "answered_calls" in col_map:
            try: answered_calls += int(r[col_map["answered_calls"]])
            except (ValueError, IndexError): pass

    # Fallback si no había columna booleana explicita "habló el agente"
    if "agente_hablo" not in col_map:
        if total_messages_agent > 0:
            conversations_with_agent = total_conversations
        else:
            conversations_bot_only = total_conversations

    return {
        "total_conversations": total_conversations,
        "conversations_with_agent": conversations_with_agent,
        "conversations_bot_only": conversations_bot_only,
        "total_agent_sessions": conversations_with_agent,
        "total_messages_user": total_messages_user,
        "total_messages_bot": total_messages_bot,
        "total_messages_agent": total_messages_agent,
        "total_templates_sent": total_templates_sent,
        "total_templates_delivered": total_templates_delivered,
        "total_templates_read": total_templates_read,
        "total_templates_responded": total_templates_responded,
        "total_templates_not_sent": total_templates_not_sent,
        "total_calls": total_calls,
        "answered_calls": answered_calls,
        "matched_columns": {k: headers[v] for k, v in col_map.items() if v < len(headers)}
    }


def detect_anomalies(headers: List[str], rows: List[List[str]], schema: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detecta anomalías en columnas numéricas utilizando la puntuación Z-Score.
    - Z-Score > 3.0 -> severidad ALTA
    - Z-Score > 2.0 -> severidad MEDIA
    """
    anomalies: List[Dict[str, Any]] = []

    for col_name, meta in schema.items():
        if meta.get("type") != "numeric":
            continue
        col_idx = meta.get("index", -1)
        stats = meta.get("stats", {})
        mean = stats.get("mean", 0.0)
        std = stats.get("std", 0.0)

        if std == 0 or col_idx < 0:
            continue

        for row_idx, r in enumerate(rows, start=2):
            if col_idx >= len(r) or r[col_idx] == "":
                continue
            try:
                val = float(r[col_idx].replace("%", "").replace(",", "."))
                z_score = abs(val - mean) / std
                if z_score >= 2.8:
                    anomalies.append({
                        "column": col_name,
                        "row_index": row_idx,
                        "value": val,
                        "z_score": round(z_score, 2),
                        "severity": "high"
                    })
                elif z_score >= 2.0:
                    anomalies.append({
                        "column": col_name,
                        "row_index": row_idx,
                        "value": val,
                        "z_score": round(z_score, 2),
                        "severity": "medium"
                    })
            except ValueError:
                pass

    return anomalies


def process_smart_tsv(content: bytes, filename: str) -> Dict[str, Any]:
    """
    Procesa un archivo TSV/CSV/Excel mediante Inteligencia Estructural.
    Combina detección de codificación, separadores, cabecera inteligente, schema discovery,
    extracción universal de métricas y detección de anomalías Z-Score.
    """
    ext = filename.lower().split(".")[-1] if "." in filename else "tsv"

    raw_rows: List[List[str]] = []
    encoding = "utf-8"
    delimiter = "\t"

    if ext in ["xlsx", "xls"]:
        wb = openpyxl.load_workbook(filename=io.BytesIO(content), data_only=True)
        sheet = wb.active
        for row in sheet.iter_rows(values_only=True):
            if any(row):
                raw_rows.append([str(cell) if cell is not None else "" for cell in row])
    else:
        encoding = detect_encoding(content)
        text = content.decode(encoding, errors="replace")
        delimiter = detect_delimiter(text, filename)
        lines = [l for l in text.splitlines() if l.strip()]
        reader = csv.reader(lines, delimiter=delimiter)
        raw_rows = list(reader)

    header_idx, headers, data_rows = find_header_row(raw_rows)
    schema = discover_schema(headers, data_rows)
    metrics = extract_metrics(headers, data_rows, schema)
    anomalies = detect_anomalies(headers, data_rows, schema)

    period = extract_period_from_filename(filename) or "requiere_confirmacion"
    report_type = detect_botmaker_report_type(headers, filename)

    high_anomalies = [a for a in anomalies if a["severity"] == "high"]

    warnings = []
    if high_anomalies:
        warnings.append({
            "row": 0,
            "field": "anomalies",
            "message": f"Se detectaron {len(high_anomalies)} anomalías estadísticas severas (Z-Score > 3.0).",
            "severity": "WARNING"
        })

    status = "VALID_WITH_WARNINGS" if warnings else "VALID"

    return {
        "status": status,
        "format": ext,
        "encoding": encoding,
        "delimiter": "\\t" if delimiter == "\t" else delimiter,
        "header_index": header_idx,
        "headers": headers,
        "total_rows": len(data_rows),
        "sample_rows": data_rows[:10],
        "period": period,
        "report_type": report_type,
        "schema": schema,
        "metrics": metrics,
        "anomalies": anomalies,
        "warnings": warnings,
        "errors": []
    }
