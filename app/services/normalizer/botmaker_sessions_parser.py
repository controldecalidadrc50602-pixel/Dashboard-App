from typing import Dict, Any, List
from app.services.normalizer.base_parser import BaseParser

class BotmakerSessionsParser(BaseParser):
    PARSER_VERSION = "botmaker-sessions-v1.0"

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

        user_val = get_val("user") or get_val("usuario") or get_val("contact")
        channel_val = get_val("channel") or get_val("canal")
        template_val = get_val("template") or get_val("plantilla")
        ts_val = get_val("timestamp") or get_val("date") or get_val("fecha") or get_val("time")
        responded_val = get_val("responded") or get_val("respondido")

        start_at = self.parse_datetime(ts_val)
        responded_bool = self.parse_bool(responded_val)

        # Si hay datos de respuesta: si no respondió, se considera abandonado/no atendido
        is_abandoned = None
        if responded_bool is not None:
            is_abandoned = not responded_bool

        if not user_val:
            warnings.append({
                "row": row_number,
                "field": "user_id",
                "message": "Fila sin usuario/contacto en sessionStartingCauses.",
                "severity": "WARNING"
            })

        quality_status = "VALID_WITH_WARNINGS" if warnings else "VALID"

        return {
            "row_number": row_number,
            "parser_version": self.PARSER_VERSION,
            "event_id": None,
            "user_id": self.clean_str(user_val),
            "channel": self.clean_str(channel_val),
            "agent": None,
            "queue": None,
            "start_at": start_at,
            "end_at": None,
            "wait_time_seconds": None,
            "duration_seconds": None,
            "messages_count": None,
            "is_abandoned": is_abandoned,
            "typification": self.clean_str(template_val),
            "quality_status": quality_status,
            "raw_data": raw_dict,
            "normalized_data": {
                "report_family": "botmaker_session_causes",
                "template": self.clean_str(template_val),
                "parsed_at_row": row_number
            },
            "warnings": warnings
        }
