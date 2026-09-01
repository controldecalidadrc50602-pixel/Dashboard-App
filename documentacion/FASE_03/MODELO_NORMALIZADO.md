# 📐 FASE 03 — Modelo de Datos Normalizado (`NormalizedRecord`)

## Definición de Tabla `normalized_records`

| Campo | Tipo | Nulable | Descripción |
|-------|------|---------|-------------|
| `id` | Integer | No | Identificador único del registro normalizado. |
| `client_id` | Integer | No | ID del cliente propietario. |
| `import_id` | Integer | No | ID de la importación RAW origen. |
| `source_code` | String | No | Código de la fuente (`botmaker`, `yeastar`, `manual`). |
| `report_type` | String | No | Familia del reporte (`users`, `operatorsSessionsDebug`, etc.). |
| `period` | String | Sí | Período de referencia (YYYY-MM). |
| `row_number` | Integer | No | Número de fila exacto en el archivo RAW original. |
| `parser_version` | String | No | Versión del parser ejecutor (ej. `botmaker-users-v1.0`). |
| `event_id` | String | Sí | ID de conversación o sesión de la plataforma. |
| `user_id` | String | Sí | ID o número de contacto del usuario final. |
| `channel` | String | Sí | Canal de atención (WhatsApp, Web, etc.). |
| `agent` | String | Sí | Agente u operador participante. |
| `queue` | String | Sí | Cola de atención o departamento. |
| `start_at` | DateTime | Sí | Marca de tiempo de inicio del evento/atención. |
| `end_at` | DateTime | Sí | Marca de tiempo de fin del evento/atención. |
| `wait_time_seconds` | Float | Sí | Tiempo de espera en segundos (NULL si no disponible). |
| `duration_seconds` | Float | Sí | Duración de atención en segundos (NULL si no disponible). |
| `messages_count` | Integer | Sí | Conteo de mensajes intercambiados (NULL si no disponible). |
| `is_abandoned` | Boolean | Sí | Indicador de abandono/sin respuesta (NULL si no disponible). |
| `typification` | String | Sí | Categorización, motivo de cierre o plantilla enviada. |
| `quality_status` | String | No | Estado de calidad de la fila (`VALID`, `VALID_WITH_WARNINGS`). |
| `raw_data` | JSON | No | Diccionario completo de datos crudos clave-valor de la fila original. |
| `normalized_data` | JSON | No | Metadata adicional estructurada del parseo. |

## Regla de Representación de Nulos
Campos no provistos en la fuente original se registran explícitamente como `NULL` en SQL y `None` en Python, evitando la conversión engañosa a `0`, `False` o timestamps actuales.
