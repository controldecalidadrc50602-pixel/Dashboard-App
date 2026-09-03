import io
import re
import csv
from typing import Dict, Any, List, Tuple, Optional
import openpyxl

def detect_encoding(content: bytes) -> str:
    """Detecta el encoding del contenido de texto (utf-8, utf-8-sig, latin-1, utf-16)."""
    encodings_to_try = ["utf-8-sig", "utf-8", "latin-1", "iso-8859-1", "utf-16"]
    for enc in encodings_to_try:
        try:
            content.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"  # Fallback tolerante


def detect_delimiter(sample_text: str, filename: str) -> str:
    """Detecta el delimitador (tabulador '\\t', coma ',', punto y coma ';') según la extensión y el texto."""
    if filename.lower().endswith(".tsv"):
        return "\t"
    
    first_line = sample_text.splitlines()[0] if sample_text else ""
    counts = {
        "\t": first_line.count("\t"),
        ",": first_line.count(","),
        ";": first_line.count(";")
    }
    best_delim = max(counts, key=counts.get)
    return best_delim if counts[best_delim] > 0 else "\t" if filename.lower().endswith(".tsv") else ","


def extract_period_from_filename(filename: str) -> Optional[str]:
    """
    Intenta deducir el período (YYYY-MM) a partir del nombre del archivo.
    Formatos comunes:
    - users-2026.09.01-20.31.tsv -> 2026-09
    - report_2026_08.csv -> 2026-08
    - 20260901.xlsx -> 2026-09
    """
    # Patrón YYYY.MM o YYYY-MM o YYYY_MM
    match = re.search(r'(20\d{2})[\.\-_](0[1-9]|1[0-2])', filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    
    # Patrón YYYYMMDD
    match_compact = re.search(r'(20\d{2})(0[1-9]|1[0-2])([0-2][0-9]|3[01])', filename)
    if match_compact:
        return f"{match_compact.group(1)}-{match_compact.group(2)}"
        
    return None


def is_description_row(row: List[str], headers: List[str]) -> bool:
    """Detecta si una fila contiene descripciones o leyendas explicativas secundarias de columnas."""
    if not row:
        return False
    row_text = " ".join(str(c) for c in row).lower()
    indicators = [
        "identificador", "descripción", "descripcion", "tiempo promedio",
        "indica si", "fecha y hora", "link a la", "número de", "numero de",
        "cantidad de veces", "nombre del agente"
    ]
    matches = sum(1 for ind in indicators if ind in row_text)
    if matches >= 2:
        return True
    long_desc_cells = sum(1 for c in row if len(str(c).strip()) > 25 and " " in str(c).strip())
    if long_desc_cells >= 3:
        return True
    return False


def detect_botmaker_report_type(headers: List[str], filename: str) -> str:
    """Detecta automáticamente el tipo de reporte Botmaker por nombre de archivo o columnas (español e inglés)."""
    fn = (filename or "").lower()
    hl = [str(h).lower() for h in headers]
    hl_str = " ".join(hl)

    # 1. Por columnas
    if any(k in hl_str for k in ["conversaciones cerradas", "tiempo medio de respuesta", "transferencias recibidas", "operatorssessions"]):
        return "operatorsSessionsDebug"
    if any(k in hl_str for k in ["plantilla", "template", "no enviado", "entregado", "leída", "leida", "respondida", "sessionstartingcauses"]):
        return "sessionStartingCauses"
    if any(k in hl_str for k in ["habló el agente", "hablo el agente", "mensajes bot", "mensajes usuario", "mensajes agente", "link conversación", "link conversacion"]):
        return "users"

    # 2. Por nombre de archivo
    if "operator" in fn or "debug" in fn:
        return "operatorsSessionsDebug"
    if "session" in fn or "cause" in fn or "plantilla" in fn:
        return "sessionStartingCauses"
    if "user" in fn:
        return "users"

    return "generic"


def analyze_file_content(content: bytes, filename: str) -> Dict[str, Any]:
    """
    Analiza el archivo RAW y extrae metadata estructural:
    encoding, delimitador, formato, encabezados, muestras de filas y período preliminar.
    """
    ext = filename.lower().split(".")[-1] if "." in filename else "txt"

    if ext in ["xlsx", "xls"]:
        return analyze_excel_content(content, filename)
    
    encoding = detect_encoding(content)
    text = content.decode(encoding, errors="replace")
    delimiter = detect_delimiter(text, filename)
    
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return {
            "format": ext,
            "encoding": encoding,
            "delimiter": delimiter,
            "headers": [],
            "sample_rows": [],
            "total_rows": 0,
            "period": extract_period_from_filename(filename) or "requiere_confirmacion",
            "report_type": "generic"
        }

    reader = csv.reader(lines, delimiter=delimiter)
    all_rows = list(reader)

    headers = all_rows[0] if all_rows else []
    
    # Filtrar fila 2 si es encabezado secundario de descripciones (operatorsSessionsDebug)
    data_rows = all_rows[1:]
    has_description_header = False
    if data_rows and is_description_row(data_rows[0], headers):
        data_rows = data_rows[1:]
        has_description_header = True

    sample_rows = data_rows[:10] if data_rows else []
    total_rows = len(data_rows)

    period = extract_period_from_filename(filename) or "requiere_confirmacion"
    report_type = detect_botmaker_report_type(headers, filename)

    return {
        "format": ext,
        "encoding": encoding,
        "delimiter": "\\t" if delimiter == "\t" else delimiter,
        "headers": headers,
        "sample_rows": sample_rows,
        "total_rows": total_rows,
        "period": period,
        "report_type": report_type,
        "has_description_header": has_description_header
    }


def analyze_excel_content(content: bytes, filename: str) -> Dict[str, Any]:
    """Analiza archivos Excel XLSX/XLS."""
    wb = openpyxl.load_workbook(filename=io.BytesIO(content), data_only=True)
    sheet = wb.active

    all_rows = []
    for row in sheet.iter_rows(values_only=True):
        if any(row):  # Filtrar filas vacías
            all_rows.append([str(cell) if cell is not None else "" for cell in row])

    headers = all_rows[0] if all_rows else []
    sample_rows = all_rows[1:11] if len(all_rows) > 1 else []
    total_rows = max(0, len(all_rows) - 1)

    return {
        "format": "xlsx",
        "encoding": "utf-8",
        "delimiter": "excel",
        "headers": headers,
        "sample_rows": sample_rows,
        "total_rows": total_rows,
        "period": extract_period_from_filename(filename) or "requiere_confirmacion"
    }
