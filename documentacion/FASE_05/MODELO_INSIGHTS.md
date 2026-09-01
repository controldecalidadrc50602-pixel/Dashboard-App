# 💡 FASE 05 — Modelo de Entidad `AnalysisInsight`

## Estructura de Tabla `analysis_insights`

| Campo | Tipo | Nulable | Descripción |
|-------|------|---------|-------------|
| `id` | Integer | No | Identificador único del insight. |
| `client_id` | Integer | No | ID del cliente evaluado. |
| `period` | String | No | Período (YYYY-MM). |
| `analysis_type` | String | No | `TARGET_COMPLIANCE`, `PERIOD_OVER_PERIOD`, `TREND`, `DATA_QUALITY`. |
| `severity` | String | No | `INFO`, `POSITIVE`, `WARNING`, `CRITICAL`, `NOT_AVAILABLE`. |
| `title` | String | No | Titular explicativo corto. |
| `description` | Text | No | Observación determinística detallada. |
| `kpi_config_id` | Integer | Sí | Referencia al KPIConfig de origen. |
| `kpi_result_id` | Integer | Sí | Referencia al KPIResult evaluado. |
| `current_value` | Float | Sí | Valor numérico del período actual. |
| `reference_value` | Float | Sí | Valor numérico del período o meta de comparación. |
| `delta` | Float | Sí | Diferencial absoluto (`current - reference`). |
| `delta_percent` | Float | Sí | Diferencial porcentual (`(delta / reference) * 100`). |
| `rule_id` | String | No | ID de la regla ejecotora (ej. `rule_target_compliance_v1`). |
| `rule_version` | String | No | Versión de la regla (`v1.0`). |
| `source_references` | JSON | No | Metadata de trazabilidad. |
| `created_at` | DateTime | No | Timestamp de generación. |
