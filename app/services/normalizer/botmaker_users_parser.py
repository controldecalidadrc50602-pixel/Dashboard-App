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

        headers_map = {h.lower(): h for h in headers}

        def get_val(fragments: List[str]) -> str:
            for frag in fragments:
                for k_lower, original_key in headers_map.items():
                    if frag in k_lower:
                        return raw_dict.get(original_key, "")
            return ""

        conv_val = get_val(["id sesión", "id sesion", "link conversación", "link conversacion", "conversation", "session"])
        user_val = get_val(["id contacto", "contacto", "número", "numero", "id usuario", "usuario", "contact", "user"])
        channel_val = get_val(["id canal", "canal", "channel"])
        hablo_agente_raw = get_val(["habló el agente", "hablo el agente"])
        agent_val = get_val(["agente", "agent", "operator"])
        
        msg_user = self.parse_int(get_val(["mensajes usuario", "user messages"])) or 0
        msg_bot = self.parse_int(get_val(["mensajes bot", "bot messages"])) or 0
        msg_agent = self.parse_int(get_val(["mensajes agente", "agent messages"])) or 0
        generic_msgs = self.parse_int(get_val(["mensajes", "messages"]))
        total_msgs = (msg_user + msg_bot + msg_agent) if (msg_user + msg_bot + msg_agent > 0) else generic_msgs

        date_val = get_val(["fecha sesión", "fecha sesion", "fecha", "date"])
        time_val = get_val(["hora sesión", "hora sesion", "hora", "time"])
        typi_val = get_val(["tipificación", "tipificacion", "typification"])
        link_val = get_val(["link conversación", "link conversacion", "link"])

        # Determinar si intervino agente
        spoke_agent = 0
        if hablo_agente_raw != "":
            s_val = str(hablo_agente_raw).strip().lower()
            if s_val in ["1", "true", "si", "sí", "yes", "t"]:
                spoke_agent = 1
        elif agent_val and agent_val.strip().lower() not in ["", "-", "ninguno", "none", "bot"]:
            spoke_agent = 1

        effective_agent = self.clean_str(agent_val) if agent_val else ("Agente" if spoke_agent == 1 else None)

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
            "agent": effective_agent,
            "queue": None,
            "start_at": start_at,
            "end_at": None,
            "wait_time_seconds": None,
            "duration_seconds": None,
            "messages_count": total_msgs,
            "is_abandoned": False if spoke_agent == 1 else None,
            "typification": self.clean_str(typi_val),
            "quality_status": quality_status,
            "raw_data": raw_dict,
            "normalized_data": {
                "report_family": "botmaker_users",
                "spoke_agent": spoke_agent,
                "user_messages": msg_user,
                "bot_messages": msg_bot,
                "agent_messages": msg_agent,
                "conversation_link": self.clean_str(link_val),
                "parsed_at_row": row_number
            },
            "warnings": warnings
        }
