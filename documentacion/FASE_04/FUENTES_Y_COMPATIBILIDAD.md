# 🌐 FASE 04 — Fuentes de Datos, Compatibilidad y Alcance

## Fuentes Soportadas en Fase 04

### 1. Botmaker Chatbot
- **Familias:** `users`, `operatorsSessionsDebug`, `sessionStartingCauses`.
- **Métricas:** `total_sessions`, `total_messages`, `total_attended_sessions`, `total_abandoned_sessions`, `avg_wait_time_seconds`, `avg_duration_seconds`.

### 2. Yeastar Extension Statistics
- **Reporte:** "Estadísticas de Llamadas de Extensión".
- **Parser:** `YeastarExtensionStatsParser` (`yeastar-ext-stats-v1.0`).
- **Métricas Extraídas:** `agent`, `messages_count` (total llamadas), `duration_seconds` (duración total conversación), `answered_calls`, `unanswered_calls`.

### 3. Yeastar Extension Call Activity
- **Reporte:** "Actividad Llamadas de Extensión".
- **Parser:** `YeastarExtensionActivityParser` (`yeastar-ext-activity-v1.0`).
- **Métricas Extraídas:** `agent`, `month` (`period`), `wait_time_seconds` (duración total timbre), `duration_seconds` (duración total conversación).

### 4. Yeastar Call Center / Queue Performance
- **Reporte:** "Rendimiento de Cola".
- **Parser:** `YeastarQueuePerformanceParser` (`yeastar-queue-perf-v1.0`).
- **Métricas Extraídas:** `queue`, `period`, `messages_count` (llamadas totales), `answered`, `abandoned`, `sla_percent`, `wait_time_seconds`, `duration_seconds`.

## Declaración Explícita de Alcance
- **Yeastar AI Reports:** FUERA DE ALCANCE ACTUAL — NO UTILIZADO.
- **Botmaker / Yeastar API Integration Directa:** FUERA DE ALCANCE ACTUAL.
