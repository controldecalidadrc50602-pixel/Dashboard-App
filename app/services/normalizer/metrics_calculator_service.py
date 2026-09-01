from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import NormalizedRecord

def calculate_base_metrics(db: Session, import_id: int) -> Dict[str, Any]:
    """
    Calcula métricas operativas base derivadas estrictamente de la tabla normalized_records.
    Cada métrica incluye documentación formal de su definición, fuente, fórmula y limitaciones.
    """
    records = db.query(NormalizedRecord).filter(NormalizedRecord.import_id == import_id).all()

    total_records = len(records)
    if total_records == 0:
        return {
            "metrics": {},
            "summary": {"total_records": 0, "status": "NO_DATA"}
        }

    # 1. Total de Sesiones / Eventos
    event_ids = [r.event_id for r in records if r.event_id]
    total_sessions = len(event_ids) if event_ids else total_records

    # 2. Mensajes Totales
    msg_counts = [r.messages_count for r in records if r.messages_count is not None]
    total_messages = sum(msg_counts) if msg_counts else None

    # 3. Tiempos de Espera
    wait_times = [r.wait_time_seconds for r in records if r.wait_time_seconds is not None]
    avg_wait_time = (sum(wait_times) / len(wait_times)) if wait_times else None

    # 4. Duraciones de Atención
    durations = [r.duration_seconds for r in records if r.duration_seconds is not None]
    avg_duration = (sum(durations) / len(durations)) if durations else None

    # 5. Sesiones Atendidas vs Abandonadas
    abandoned_list = [r.is_abandoned for r in records if r.is_abandoned is not None]
    total_abandoned = sum(1 for a in abandoned_list if a is True) if abandoned_list else None
    total_attended = sum(1 for r in records if r.agent or (r.is_abandoned is False))

    # 6. Usuarios Únicos y Agentes Únicos
    unique_users = len(set(r.user_id for r in records if r.user_id))
    unique_agents = len(set(r.agent for r in records if r.agent))

    # 7. Desglose de Tipificaciones
    typification_counts: Dict[str, int] = {}
    for r in records:
        t = r.typification or "Sin Tipificar"
        typification_counts[t] = typification_counts.get(t, 0) + 1

    return {
        "summary": {
            "total_records": total_records,
            "unique_users": unique_users,
            "unique_agents": unique_agents
        },
        "metrics": {
            "total_sessions": {
                "name": "Total de Sesiones / Conversaciones",
                "value": total_sessions,
                "unit": "sesiones",
                "definition": "Número de eventos o sesiones únicas procesadas en el reporte.",
                "formula": "COUNT(event_id)",
                "limitations": "Depende de la presencia de IDs de conversación en el origen."
            },
            "total_messages": {
                "name": "Total de Mensajes Intercambiados",
                "value": total_messages,
                "unit": "mensajes",
                "definition": "Suma total de mensajes intercambiados entre bot, agentes y usuarios.",
                "formula": "SUM(messages_count)",
                "limitations": "Disponible únicamente si la fuente provee el conteo de mensajes."
            },
            "total_attended_sessions": {
                "name": "Sesiones Atendidas",
                "value": total_attended,
                "unit": "sesiones",
                "definition": "Sesiones asignadas a un agente o marcadas como respondidas.",
                "formula": "COUNT(agent != NULL OR is_abandoned == False)",
                "limitations": "Representa atención efectiva por parte de operadores o canal."
            },
            "total_abandoned_sessions": {
                "name": "Sesiones Abandonadas / Sin Respuesta",
                "value": total_abandoned,
                "unit": "sesiones",
                "definition": "Sesiones donde la interacción finalizó sin respuesta del operador.",
                "formula": "COUNT(is_abandoned == True)",
                "limitations": "Es NULL si el formato de origen no reporta estado de respuesta."
            },
            "avg_wait_time_seconds": {
                "name": "Tiempo Promedio de Espera",
                "value": round(avg_wait_time, 2) if avg_wait_time is not None else None,
                "unit": "segundos",
                "definition": "Tiempo transcurrido desde la solicitud hasta la atención inicial.",
                "formula": "AVG(wait_time_seconds)",
                "limitations": "Calculado únicamente sobre filas que contengan marcas de tiempo de espera."
            },
            "avg_duration_seconds": {
                "name": "Duración Promedio de Atención",
                "value": round(avg_duration, 2) if avg_duration is not None else None,
                "unit": "segundos",
                "definition": "Tiempo total transcurrido desde el inicio de atención hasta el cierre.",
                "formula": "AVG(duration_seconds)",
                "limitations": "Es NULL si no se dispone de marcas de tiempo de inicio y fin."
            }
        },
        "typifications_breakdown": typification_counts
    }
