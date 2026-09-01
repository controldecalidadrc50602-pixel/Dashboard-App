from typing import Dict, Any, List
from app.services.normalizer.base_parser import BaseParser

class YeastarExtensionStatsParser(BaseParser):
    PARSER_VERSION = "yeastar-ext-stats-v1.0"

    def parse_row(self, row: List[str], headers: List[str], row_number: int) -> Dict[str, Any]:
        raw_dict = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
        warnings = []

        headers_map = {h.lower(): h for h in headers}

        def get_val(key_fragment: str) -> str:
            for k_lower, original_key in headers_map.items():
                if key_fragment in k_lower:
                    return raw_dict.get(original_key, "")
            return ""

        ext_val = get_val("extensión") or get_val("extension")
        type_val = get_val("tipo") or get_val("comunicación") or get_val("communication")
        ans_val = get_val("contestada") or get_val("answered")
        unans_val = get_val("no contestada") or get_val("unanswered")
        total_val = get_val("total")
        dur_val = get_val("duración total de conversación") or get_val("conversation duration") or get_val("duracion")

        duration_sec = self.parse_duration_seconds(dur_val)

        if not ext_val:
            warnings.append({"row": row_number, "field": "extension", "message": "Fila sin extensión especificada.", "severity": "WARNING"})

        return {
            "row_number": row_number,
            "parser_version": self.PARSER_VERSION,
            "event_id": f"ext_{ext_val}_{row_number}",
            "user_id": None,
            "channel": f"Yeastar-{type_val}" if type_val else "Yeastar-Ext",
            "agent": self.clean_str(ext_val),
            "queue": None,
            "start_at": None,
            "end_at": None,
            "wait_time_seconds": None,
            "duration_seconds": duration_sec,
            "messages_count": self.parse_int(total_val),
            "is_abandoned": None,
            "typification": self.clean_str(type_val),
            "quality_status": "VALID_WITH_WARNINGS" if warnings else "VALID",
            "raw_data": raw_dict,
            "normalized_data": {
                "report_family": "yeastar_extension_stats",
                "answered_calls": self.parse_int(ans_val),
                "unanswered_calls": self.parse_int(unans_val)
            },
            "warnings": warnings
        }


class YeastarExtensionActivityParser(BaseParser):
    PARSER_VERSION = "yeastar-ext-activity-v1.0"

    def parse_row(self, row: List[str], headers: List[str], row_number: int) -> Dict[str, Any]:
        raw_dict = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
        warnings = []

        headers_map = {h.lower(): h for h in headers}

        def get_val(key_fragment: str) -> str:
            for k_lower, original_key in headers_map.items():
                if key_fragment in k_lower:
                    return raw_dict.get(original_key, "")
            return ""

        month_val = get_val("mes") or get_val("month")
        ext_val = get_val("extensión") or get_val("extension")
        ring_val = get_val("duración total de timbre") or get_val("ring duration")
        conv_val = get_val("duración total de conversación") or get_val("conversation duration")
        ans_val = get_val("contestada") or get_val("answered")

        ring_sec = self.parse_duration_seconds(ring_val)
        conv_sec = self.parse_duration_seconds(conv_val)

        return {
            "row_number": row_number,
            "parser_version": self.PARSER_VERSION,
            "event_id": f"act_{ext_val}_{row_number}",
            "user_id": None,
            "channel": "Yeastar-Activity",
            "agent": self.clean_str(ext_val),
            "queue": None,
            "start_at": None,
            "end_at": None,
            "wait_time_seconds": ring_sec,
            "duration_seconds": conv_sec,
            "messages_count": self.parse_int(ans_val),
            "is_abandoned": None,
            "typification": None,
            "quality_status": "VALID_WITH_WARNINGS" if warnings else "VALID",
            "raw_data": raw_dict,
            "normalized_data": {
                "report_family": "yeastar_extension_activity",
                "month": self.clean_str(month_val)
            },
            "warnings": warnings
        }


class YeastarQueuePerformanceParser(BaseParser):
    PARSER_VERSION = "yeastar-queue-perf-v1.0"

    def parse_row(self, row: List[str], headers: List[str], row_number: int) -> Dict[str, Any]:
        raw_dict = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
        warnings = []

        headers_map = {h.lower(): h for h in headers}

        def get_val(key_fragment: str) -> str:
            for k_lower, original_key in headers_map.items():
                if key_fragment in k_lower:
                    return raw_dict.get(original_key, "")
            return ""

        queue_val = get_val("cola") or get_val("queue")
        total_val = get_val("llamadas totales") or get_val("total calls")
        ans_val = get_val("contestada") or get_val("answered")
        abandoned_val = get_val("abandonada") or get_val("abandoned")
        wait_val = get_val("promedio tiempo de espera") or get_val("avg wait")
        handle_val = get_val("avg handle time") or get_val("tiempo promedio de conversación")
        sla_val = get_val("sla")

        wait_sec = self.parse_duration_seconds(wait_val)
        handle_sec = self.parse_duration_seconds(handle_val)

        return {
            "row_number": row_number,
            "parser_version": self.PARSER_VERSION,
            "event_id": f"queue_{queue_val}_{row_number}",
            "user_id": None,
            "channel": "Yeastar-Queue",
            "agent": None,
            "queue": self.clean_str(queue_val),
            "start_at": None,
            "end_at": None,
            "wait_time_seconds": wait_sec,
            "duration_seconds": handle_sec,
            "messages_count": self.parse_int(total_val),
            "is_abandoned": None,
            "typification": None,
            "quality_status": "VALID_WITH_WARNINGS" if warnings else "VALID",
            "raw_data": raw_dict,
            "normalized_data": {
                "report_family": "yeastar_queue_performance",
                "answered": self.parse_int(ans_val),
                "abandoned": self.parse_int(abandoned_val),
                "sla_percent": self.parse_float(sla_val)
            },
            "warnings": warnings
        }
