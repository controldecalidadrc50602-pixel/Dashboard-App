from typing import Dict, Any, List
from app.services.normalizer.base_parser import BaseParser

class BotmakerUsersParser(BaseParser):
    PARSER_VERSION = "botmaker-users-v1.0"

    def parse_row(
        self,
        row: List[str],
        headers: List[str],
        row_number: int
    ) -> Dict[str, Any]:
        raw_dict = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
        warnings = []

        # Mapeo difuso de encabezados (case-insensitive)
        headers_map = {h.lower(): h for h in headers}

        def get_val(key_fragment: str) -> str:
            for k_lower, original_key in headers_map.items():
                if key_fragment in k_lower:
                    return raw_dict.get(original_key, "")
            return ""

        conv_val = get_val("conversation") or get_val("sesion") or get_val("session")
        user_val = get_val("contact") or get_val("contacto") or get_val("usuario") or get_val("user")
        channel_val = get_val("channel") or get_val("canal")
        agent_val = get_val("agent") or get_val("agente") or get_val("operator")
        messages_val = get_val("messages") or get_val("mensajes")
        date_val = get_val("date") or get_val("fecha")
        time_val = get_val("time") or get_val("hora")
        typi_val = get_val("typification") or get_val("tipificación") or get_val("tipificacion")

        # Reconstrucción de timestamp
        start_at = None
        if date_val and time_val:
            start_at = self.parse_datetime(f"{date_val.strip()} {time_val.strip()}")
        elif date_val:
            start_at = self.parse_datetime(date_val)

        if not conv_val and not user_val:
            warnings.append({
                "row": row_number,
                "field": "event_id/user_id",
                "message": "Fila no contiene identificador claro de conversación o usuario.",
                "severity": "WARNING"
            })

        quality_status = "VALID_WITH_WARNINGS" if warnings else "VALID"

        return {
            "row_number": row_number,
            "parser_version": self.PARSER_VERSION,
            "event_id": self.clean_str(conv_val),
            "user_id": self.clean_str(user_val),
            "channel": self.clean_str(channel_val),
            "agent": self.clean_str(agent_val),
            "queue": None,  # NOT_AVAILABLE en este formato de reporte
            "start_at": start_at,
            "end_at": None,
            "wait_time_seconds": None,
            "duration_seconds": None,
            "messages_count": self.parse_int(messages_val),
            "is_abandoned": None,
            "typification": self.clean_str(typi_val),
            "quality_status": quality_status,
            "raw_data": raw_dict,
            "normalized_data": {
                "report_family": "botmaker_users",
                "parsed_at_row": row_number
            },
            "warnings": warnings
        }
