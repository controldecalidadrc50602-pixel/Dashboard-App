# 📐 FASE 04 — Modelo de Datos del Motor KPI (`KPIConfig` & `KPIResult`)

## 1. Tabla `kpi_configs`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer | ID de la configuración de KPI. |
| `client_id` | Integer | ID del cliente al que pertenece el KPI. |
| `kpi_code` | String | Identificador único del KPI (ej. `sla_citas`, `abandon_rate`). |
| `kpi_name` | String | Nombre comercial (ej. `SLA de Citas`). |
| `description` | Text | Descripción de la regla o meta. |
| `source_code` | String | Fuente de origen (`botmaker`, `yeastar`, `manual`). |
| `report_type` | String | Familia de reporte de origen (`users`, `queue`, `extension`). |
| `target_value` | Float | Objetivo configurado (NULL representa `NO_TARGET`). |
| `formula_type` | String | Algoritmo determinista (`ratio`, `difference`, `percentage_gap`, `direct`). |
| `formula_expression` | String | Representación textual legible de la regla de negocio. |
| `input_metrics` | JSON | Lista de claves de entrada requeridas (ej. `["answered", "total"]`). |
| `direction` | String | `higher_is_better`, `lower_is_better`, `range`. |
| `unit` | String | `percentage`, `count`, `seconds`, `duration`, `NOT_VERIFIED`. |
| `period_frequency` | String | `monthly`, `weekly`, `daily`. |
| `thresholds` | JSON | Umbrales de advertencia o peligro (`warning`, `danger`). |
| `is_active` | Boolean | Estado activo/desactivado del KPI. |
| `version` | String | Versión de la definición (`v1.0`). |

## 2. Tabla `kpi_results`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer | ID único del resultado evaluado. |
| `client_id` | Integer | ID del cliente. |
| `kpi_config_id` | Integer | Referencia a la regla `KPIConfig` evaluada. |
| `import_id` | Integer | ID del archivo RAW de origen utilizado. |
| `period` | String | Período evaluado (YYYY-MM). |
| `kpi_code` | String | Código del KPI. |
| `source_code` | String | Fuente utilizada. |
| `value` | Float | Valor numérico calculado (NULL si datos no disponibles). |
| `target_value` | Float | Meta al momento del cálculo. |
| `status` | String | `NO_DATA`, `NOT_AVAILABLE`, `NO_TARGET`, `ON_TARGET`, `BELOW_TARGET`, `ABOVE_TARGET`. |
| `status_color` | String | Color para interfaz (`green`, `yellow`, `red`, `gray`). |
| `formula_used` | String | Fórmula ejecutada. |
| `input_values` | JSON | Diccionario de métricas de entrada reales utilizadas. |
| `traceability_info` | JSON | Payload completo de trazabilidad hasta el archivo RAW. |
