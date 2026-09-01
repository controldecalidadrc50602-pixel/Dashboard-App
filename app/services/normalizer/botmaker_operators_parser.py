from typing import Dict, Any, List
from app.services.normalizer.base_parser import BaseParser

class BotmakerOperatorsParser(BaseParser):
    PARSER_VERSION = "botmaker-operators-v1.0"

    def parse_row(
        self,
        row: List[str],
        headers: List[str],
        row_number: int
    ) -> Dict[str, Any]:
        raw_dict = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
        warnings = []

        headers_map = {h.lower(): h for h in headers}

        def get_val(key_fragment: str) -> str:
            for k_lower, original_key in headers_map.items():
                if key_fragment in k_lower:
                    return raw_dict.get(original_key, "")
            return ""

        session_val = get_val("session") or get_val("sesion")
        user_val = get_val("user") or get_val("usuario")
        start_val = get_val("start") or get_val("inicio")
        end_val = get_val("end") or get_val("fin")
        agent_val = get_val("agent") or get_val("agente") or get_val("operator")
        queue_val = get_val("queue") or get_val("cola")
        typi_val = get_val("typification") or get_val("tipificación") or get_val("tipificacion")
        wait_val = get_val("wait") or get_val("espera")

        start_at = self.parse_datetime(start_val)
        end_at = self.parse_datetime(end_val)
        wait_seconds = self.parse_duration_seconds(wait_val)

        duration_seconds = None
        if start_at and end_at:
            duration_seconds = max(0.0, (end_at - start_at).total_seconds())

        if not session_val and not user_val:
            warnings.append({
                "row": row_number,
                "field": "event_id/user_id",
                "message": "Sesión sin identificador único en operatorsSessionsDebug.",
                "severity": "WARNING"
            })

        quality_status = "VALID_WITH_WARNINGS" if warnings else "VALID"

        return {
            "row_number": row_number,
            "parser_version": self.PARSER_VERSION,
            "event_id": self.clean_str(session_val),
            "user_id": self.clean_str(user_val),
            "channel": None,  # NOT_AVAILABLE en este reporte específico
            "agent": self.clean_str(agent_val),
            "queue": self.clean_str(queue_val),
            "start_at": start_at,
            "end_at": end_at,
            "wait_time_seconds": wait_seconds,
            "duration_seconds": duration_seconds,
            "messages_count": None,
            "is_abandoned": None,
            "typification": self.clean_str(typi_val),
            "quality_status": quality_status,
            "raw_data": raw_dict,
            "normalized_data": {
                "report_family": "botmaker_operators_sessions",
                "parsed_at_row": row_number
            },
            "warnings": warnings
        }
