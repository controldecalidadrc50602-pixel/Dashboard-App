import csv
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session

from app.models import ReportImport, NormalizedRecord
from app.services.file_storage_service import read_raw_file
from app.services.detector_service import analyze_file_content

from app.services.normalizer.botmaker_users_parser import BotmakerUsersParser
from app.services.normalizer.botmaker_operators_parser import BotmakerOperatorsParser
from app.services.normalizer.botmaker_sessions_parser import BotmakerSessionsParser
from app.services.normalizer.yeastar_parsers import (
    YeastarExtensionStatsParser,
    YeastarExtensionActivityParser,
    YeastarQueuePerformanceParser
)
from app.services.normalizer.base_parser import BaseParser

class GenericParser(BaseParser):
    PARSER_VERSION = "generic-v1.0"

    def parse_row(self, row: List[str], headers: List[str], row_number: int) -> Dict[str, Any]:
        raw_dict = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
        return {
            "row_number": row_number,
            "parser_version": self.PARSER_VERSION,
            "event_id": None,
            "user_id": None,
            "channel": None,
            "agent": None,
            "queue": None,
            "start_at": None,
            "end_at": None,
            "wait_time_seconds": None,
            "duration_seconds": None,
            "messages_count": None,
            "is_abandoned": None,
            "typification": None,
            "quality_status": "VALID",
            "raw_data": raw_dict,
            "normalized_data": {"report_family": "generic"},
            "warnings": []
        }


def select_parser(source_code: str, report_type: str) -> BaseParser:
    """Selecciona la instancia adecuada del parser según la fuente y el tipo de reporte."""
    source = (source_code or "").lower()
    rep = (report_type or "").lower()

    if source == "botmaker":
        if "user" in rep:
            return BotmakerUsersParser()
        elif "operator" in rep or "debug" in rep:
            return BotmakerOperatorsParser()
        elif "session" in rep or "cause" in rep:
            return BotmakerSessionsParser()
        return BotmakerUsersParser()
    elif source == "yeastar":
        if "stats" in rep or "extension" in rep:
            return YeastarExtensionStatsParser()
        elif "activity" in rep:
            return YeastarExtensionActivityParser()
        elif "queue" in rep or "call center" in rep or "performance" in rep:
            return YeastarQueuePerformanceParser()
        return YeastarExtensionStatsParser()

    return GenericParser()



def process_and_normalize_import(db: Session, import_id: int) -> Tuple[ReportImport, Dict[str, Any]]:
    """
    Lee de forma inmutable el archivo RAW guardado, lo procesa línea por línea con el parser asignado,
    elimina registros previas (soporte de reprocesamiento idempotente) y guarda los NormalizedRecords.
    """
    imp = db.query(ReportImport).filter(ReportImport.id == import_id).first()
    if not imp:
        raise ValueError("Importación no encontrada")

    parser = select_parser(imp.source_code, imp.report_type)

    # 1. Eliminar registros normalizados previos (Reprocesabilidad inmutable)
    db.query(NormalizedRecord).filter(NormalizedRecord.import_id == import_id).delete()
    db.commit()

    # 2. Leer contenido RAW almacenado
    content = read_raw_file(imp.storage_path)
    analysis = analyze_file_content(content, imp.original_filename)

    headers = analysis.get("headers", [])
    file_format = analysis.get("format", "tsv")

    all_rows = []
    if file_format in ["csv", "tsv", "txt"]:
        enc = analysis.get("encoding", "utf-8")
        delim = analysis.get("delimiter", "\t")
        if delim == "\\t":
            delim = "\t"
        text = content.decode(enc, errors="replace")
        reader = csv.reader([l for l in text.splitlines() if l.strip()], delimiter=delim)
        all_rows = list(reader)
    else:
        all_rows = [headers] + analysis.get("sample_rows", [])

    if not headers and all_rows:
        headers = all_rows[0]

    normalized_objects = []
    total_warnings_count = 0
    valid_count = 0
    warnings_count = 0

    # 3. Iterar por cada fila original (Comenzando en fila 2)
    for idx, row in enumerate(all_rows[1:], start=2):
        parsed = parser.parse_row(row, headers, row_number=idx)

        # Omitir fila de encabezado secundario de descripciones
        if parsed.get("is_description_header"):
            continue

        nr = NormalizedRecord(
            client_id=imp.client_id,
            import_id=imp.id,
            source_code=imp.source_code,
            report_type=imp.report_type or "generic",
            period=imp.period,
            row_number=parsed["row_number"],
            parser_version=parsed["parser_version"],
            event_id=parsed["event_id"],
            user_id=parsed["user_id"],
            channel=parsed["channel"],
            agent=parsed["agent"],
            queue=parsed["queue"],
            start_at=parsed["start_at"],
            end_at=parsed["end_at"],
            wait_time_seconds=parsed["wait_time_seconds"],
            duration_seconds=parsed["duration_seconds"],
            messages_count=parsed["messages_count"],
            is_abandoned=parsed["is_abandoned"],
            typification=parsed["typification"],
            quality_status=parsed["quality_status"],
            raw_data=parsed["raw_data"],
            normalized_data=parsed["normalized_data"],
            warnings=parsed["warnings"]
        )

        normalized_objects.append(nr)
        if parsed["warnings"]:
            warnings_count += 1
            total_warnings_count += len(parsed["warnings"])
        else:
            valid_count += 1

    # 4. Guardar en bloque en la BD
    db.bulk_save_objects(normalized_objects)
    
    # 5. Cálculo de métricas específicas Botmaker según requerimiento
    calculated_metrics: Dict[str, Any] = {}
    rep_type_l = (imp.report_type or "").lower()

    if "operator" in rep_type_l or "debug" in rep_type_l:
        total_sessions = len(normalized_objects)
        total_closed = sum(nr.normalized_data.get("closed_conversations", 0) for nr in normalized_objects)
        times = [nr.normalized_data.get("avg_response_time_seconds") for nr in normalized_objects if nr.normalized_data.get("avg_response_time_seconds") is not None]
        avg_resp = round(sum(times) / len(times), 2) if times else None
        transfers = sum(nr.normalized_data.get("transfers_received", 0) for nr in normalized_objects)
        agents = sorted(list(set(nr.agent for nr in normalized_objects if nr.agent)))
        typs: Dict[str, int] = {}
        for nr in normalized_objects:
            t = nr.typification or "Sin Tipificar"
            typs[t] = typs.get(t, 0) + 1

        calculated_metrics = {
            "total_agent_sessions": total_sessions,
            "total_closed_conversations": total_closed,
            "avg_response_time": avg_resp,
            "total_transfers_received": transfers,
            "agents_list": agents,
            "typifications": typs
        }
    elif "user" in rep_type_l:
        total_convs = len(normalized_objects)
        convs_agent = sum(1 for nr in normalized_objects if nr.normalized_data.get("spoke_agent") == 1)
        convs_bot = total_convs - convs_agent
        msg_user_tot = sum(nr.normalized_data.get("user_messages", 0) for nr in normalized_objects)
        msg_bot_tot = sum(nr.normalized_data.get("bot_messages", 0) for nr in normalized_objects)
        msg_agent_tot = sum(nr.normalized_data.get("agent_messages", 0) for nr in normalized_objects)

        calculated_metrics = {
            "total_conversations": total_convs,
            "conversations_with_agent": convs_agent,
            "conversations_bot_only": convs_bot,
            "total_messages_user": msg_user_tot,
            "total_messages_bot": msg_bot_tot,
            "total_messages_agent": msg_agent_tot
        }
    elif "session" in rep_type_l or "cause" in rep_type_l or "plantilla" in rep_type_l:
        total_sent = sum(1 for nr in normalized_objects if nr.normalized_data.get("sent") is True)
        total_delivered = sum(1 for nr in normalized_objects if nr.normalized_data.get("delivered") is True)
        total_read = sum(1 for nr in normalized_objects if nr.normalized_data.get("read") is True)
        total_responded = sum(1 for nr in normalized_objects if nr.normalized_data.get("responded") is True)
        total_failed = sum(1 for nr in normalized_objects if nr.normalized_data.get("failed") is True)
        new_users = sum(1 for nr in normalized_objects if nr.normalized_data.get("new_user") is True)

        calculated_metrics = {
            "total_templates_sent": total_sent,
            "total_templates_delivered": total_delivered,
            "total_templates_read": total_read,
            "total_templates_responded": total_responded,
            "total_templates_failed": total_failed,
            "new_users": new_users
        }

    # Actualizar estado y metadata del ReportImport
    meta = dict(imp.metadata_info or {})
    meta["calculated_metrics"] = calculated_metrics
    imp.metadata_info = meta

    final_status = "PROCESSED_WITH_WARNINGS" if warnings_count > 0 else "PROCESSED"
    imp.status = final_status
    db.commit()
    db.refresh(imp)

    summary = {
        "import_id": imp.id,
        "parser_version": parser.PARSER_VERSION,
        "total_rows_processed": len(normalized_objects),
        "valid_records": valid_count,
        "records_with_warnings": warnings_count,
        "total_warnings": total_warnings_count,
        "status": final_status,
        "calculated_metrics": calculated_metrics
    }

    return imp, summary
