# 📊 FASE 03 — Catálogo de Métricas Operativas Base

## Métricas Derivadas de `NormalizedRecord`

### 1. `total_sessions`
- **Nombre:** Total de Sesiones / Conversaciones
- **Unidad:** sesiones
- **Fórmula:** `COUNT(event_id)`
- **Definición:** Conteo total de eventos de interacción registrados en la fuente.
- **Limitaciones:** Depende de la presencia de identificadores de sesión en la fuente original.

### 2. `total_messages`
- **Nombre:** Total de Mensajes Intercambiados
- **Unidad:** mensajes
- **Fórmula:** `SUM(messages_count)`
- **Definición:** Suma acumulada de mensajes enviados y recibidos.
- **Limitaciones:** `NULL` si la fuente no provee conteo de mensajes.

### 3. `total_attended_sessions`
- **Nombre:** Sesiones Atendidas
- **Unidad:** sesiones
- **Fórmula:** `COUNT(agent != NULL OR is_abandoned == False)`
- **Definición:** Conteo de interacciones asignadas a un operador humano o respondidas por la plataforma.
- **Limitaciones:** Representa atención efectiva por parte del canal.

### 4. `total_abandoned_sessions`
- **Nombre:** Sesiones Abandonadas / Sin Respuesta
- **Unidad:** sesiones
- **Fórmula:** `COUNT(is_abandoned == True)`
- **Definición:** Sesiones en las que el usuario no recibió atención o respuesta.
- **Limitaciones:** `NULL` si el formato de origen no reporta estados de respuesta.

### 5. `avg_wait_time_seconds`
- **Nombre:** Tiempo Promedio de Espera
- **Unidad:** segundos
- **Fórmula:** `AVG(wait_time_seconds)`
- **Definición:** Tiempo medio transcurrido entre el ingreso del usuario y la primera atención.
- **Limitaciones:** Calculado únicamente sobre filas que contengan marcas de tiempo de espera.

### 6. `avg_duration_seconds`
- **Nombre:** Duración Promedio de Atención
- **Unidad:** segundos
- **Fórmula:** `AVG(duration_seconds)`
- **Definición:** Tiempo medio de duración de las sesiones atendidas.
- **Limitaciones:** `NULL` si el reporte no contiene timestamps de inicio y fin.
