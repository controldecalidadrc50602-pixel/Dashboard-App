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

        def get_val(fragments: List[str]) -> str:
            # Prioridad 1: Coincidencia exacta
            for frag in fragments:
                for k_lower, original_key in headers_map.items():
                    if frag == k_lower:
                        return raw_dict.get(original_key, "")
            # Prioridad 2: Subcadena excluyendo negaciones explícitas
            for frag in fragments:
                for k_lower, original_key in headers_map.items():
                    if frag in k_lower:
                        if frag in ["enviado", "sent"] and any(neg in k_lower for neg in ["no ", "not ", "fall"]):
                            continue
                        return raw_dict.get(original_key, "")
            return ""

        def to_bool(val: Any) -> bool:
            if val is None:
                return False
            v = str(val).strip().lower()
            return v in ["true", "1", "si", "sí", "verdadero", "yes", "t"]

        user_val = get_val(["id contacto", "contacto", "id usuario", "usuario", "contact", "user"])
        channel_val = get_val(["id canal", "canal", "channel"])
        template_val = get_val(["nombre plantilla/notificación", "nombre plantilla", "plantilla", "template"])
        ts_val = get_val(["fecha/tiempo inicio sesión", "fecha/tiempo inicio sesion", "fecha/tiempo envío", "timestamp", "inicio", "date"])
        
        new_user = to_bool(get_val(["usuario nuevo", "new user"]))
        failed = to_bool(get_val(["no enviado", "failed"]))
        sent = to_bool(get_val(["enviado", "sent"]))
        delivered = to_bool(get_val(["entregado", "delivered"]))
        read = to_bool(get_val(["leída", "leida", "read"]))
        responded = to_bool(get_val(["respondida", "responded"]))
        fail_reason = get_val(["razón falla envío", "razon falla envio", "detalle falla envío"])
        agent_groups = get_val(["grupos agente", "agent groups"])

        # Inferencia lógica: si fue entregado o leído, fue enviado
        if (delivered or read or responded) and not failed:
            sent = True

        start_at = self.parse_datetime(ts_val)

        is_abandoned = None
        if responded:
            is_abandoned = False
        elif failed:
            is_abandoned = True

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
                "template_name": self.clean_str(template_val),
                "sent": sent,
                "delivered": delivered,
                "read": read,
                "responded": responded,
                "failed": failed,
                "new_user": new_user,
                "fail_reason": self.clean_str(fail_reason),
                "agent_groups": self.clean_str(agent_groups),
                "parsed_at_row": row_number
            },
            "warnings": warnings
        }
