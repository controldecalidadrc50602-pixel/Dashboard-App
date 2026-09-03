from typing import Dict, Any, List
from app.services.normalizer.base_parser import BaseParser
from app.services.detector_service import is_description_row

class BotmakerOperatorsParser(BaseParser):
    PARSER_VERSION = "botmaker-operators-v1.0"

    def parse_row(
        self,
        row: List[str],
        headers: List[str],
        row_number: int
    ) -> Dict[str, Any]:
        # Detección y descarte de fila de descripciones secundaria (como la fila 2 de operatorsSessionsDebug)
        if row_number == 2 and is_description_row(row, headers):
            return {"is_description_header": True, "row_number": row_number}

        raw_dict = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
        warnings = []

        headers_map = {h.lower(): h for h in headers}

        def get_val(fragments: List[str]) -> str:
            for frag in fragments:
                for k_lower, original_key in headers_map.items():
                    if frag in k_lower:
                        return raw_dict.get(original_key, "")
            return ""

        session_val = get_val(["id sesión", "id sesion", "session", "sesion", "link conversación", "link conversacion"])
        user_val = get_val(["id usuario", "usuario", "id contacto", "contacto", "user", "contact"])
        start_val = get_val(["fecha/tiempo inicio sesión", "fecha/tiempo inicio sesion", "inicio", "start"])
        end_val = get_val(["fecha/tiempo cierre", "cierre", "end", "fin"])
        agent_val = get_val(["nombre agente", "agente", "agent", "operator"])
        agent_id_val = get_val(["id agente", "agent id"])
        queue_val = get_val(["cola", "queue"])
        typi_val = get_val(["tipificación", "tipificacion", "typification"])

        in_progress_val = get_val(["conversaciones en curso", "in progress"])
        closed_val = get_val(["conversaciones cerradas", "closed"])
        postponed_val = get_val(["pospuestas", "postponed"])
        avg_response_val = get_val(["tiempo medio de respuesta", "avg response time", "espera", "wait"])
        answers_count_val = get_val(["cantidad de respuestas", "answers count"])
        transfers_rec_val = get_val(["transferencias recibidas", "transfers received"])
        transfers_made_val = get_val(["transferencias realizadas", "transfers made"])
        link_val = get_val(["link conversación", "link conversacion", "link"])

        closed_convs = self.parse_int(closed_val) or 0
        in_progress_convs = self.parse_int(in_progress_val) or 0
        postponed_convs = self.parse_int(postponed_val) or 0
        transfers_received = self.parse_int(transfers_rec_val) or 0
        transfers_made = self.parse_int(transfers_made_val) or 0
        answers_count = self.parse_int(answers_count_val) or 0

        start_at = self.parse_datetime(start_val)
        end_at = self.parse_datetime(end_val)
        
        # Parsear tiempo medio de respuesta a segundos numéricos (ignorar '-' o vacíos)
        wait_seconds = self.parse_duration_seconds(avg_response_val)

        duration_seconds = None
        if start_at and end_at:
            duration_seconds = max(0.0, (end_at - start_at).total_seconds())

        if not session_val and not user_val and not agent_val:
            warnings.append({
                "row": row_number,
                "field": "event_id/agent",
                "message": "Sesión sin identificador único o agente en operatorsSessionsDebug.",
                "severity": "WARNING"
            })

        quality_status = "VALID_WITH_WARNINGS" if warnings else "VALID"

        return {
            "row_number": row_number,
            "parser_version": self.PARSER_VERSION,
            "event_id": self.clean_str(session_val),
            "user_id": self.clean_str(user_val),
            "channel": None,
            "agent": self.clean_str(agent_val),
            "queue": self.clean_str(queue_val),
            "start_at": start_at,
            "end_at": end_at,
            "wait_time_seconds": wait_seconds,
            "duration_seconds": duration_seconds,
            "messages_count": answers_count if answers_count > 0 else None,
            "is_abandoned": None,
            "typification": self.clean_str(typi_val),
            "quality_status": quality_status,
            "raw_data": raw_dict,
            "normalized_data": {
                "report_family": "botmaker_operators_sessions",
                "agent_id": self.clean_str(agent_id_val),
                "closed_conversations": closed_convs,
                "in_progress_conversations": in_progress_convs,
                "postponed": postponed_convs,
                "transfers_received": transfers_received,
                "transfers_made": transfers_made,
                "answers_count": answers_count,
                "avg_response_time_str": self.clean_str(avg_response_val),
                "avg_response_time_seconds": wait_seconds,
                "conversation_link": self.clean_str(link_val),
                "parsed_at_row": row_number
            },
            "warnings": warnings
        }
