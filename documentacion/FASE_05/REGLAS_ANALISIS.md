# 📜 FASE 05 — Catálogo de Reglas Determinísticas RC506

## 1. `rule_target_compliance_v1`
- **Tipo:** `TARGET_COMPLIANCE`
- **Entradas:** `KPIResult.value`, `KPIResult.target_value`, `KPIResult.status`
- **Lógica:**
  - Si `status == ON_TARGET` ➔ `POSITIVE` ("Meta Alcanzada")
  - Si `status == BELOW_TARGET` / `ABOVE_TARGET` ➔ `WARNING` / `CRITICAL` ("Desviación de Meta")
  - Si `status == NO_TARGET` ➔ `INFO` ("Sin Meta Configurada")

## 2. `rule_period_over_period_v1`
- **Tipo:** `PERIOD_OVER_PERIOD`
- **Entradas:** `KPIResult` período actual vs período anterior inmediatamente disponible.
- **Lógica:**
  - `delta = current_val - prev_val`
  - `delta_percent = (delta / prev_val) * 100`
  - Asigna severidad `POSITIVE` o `WARNING` según la direccionalidad (`higher_is_better` vs `lower_is_better`).

## 3. `rule_trend_v1`
- **Tipo:** `TREND`
- **Entradas:** Histórico de `KPIResult` de los últimos 3+ períodos.
- **Lógica:**
  - `improving`: Crecimiento monótono en 3 períodos.
  - `declining`: Caída monótona en 3 períodos.
  - `stable`: Desviación dentro del umbral de tolerancia.

## 4. `rule_data_quality_v1`
- **Tipo:** `DATA_QUALITY`
- **Entradas:** Evaluaciones con `status == NOT_AVAILABLE`
- **Lógica:** Reporta ausencia o insuficiencia de datos en la fuente original.
