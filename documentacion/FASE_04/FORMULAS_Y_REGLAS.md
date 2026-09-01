# 🧮 FASE 04 — Motor de Fórmulas y Reglas de Evaluación Deterministas

## Principios de Seguridad
- **Sin `eval()`:** Cero ejecución arbitraria de cadenas de texto o scripts en Python.
- **Fórmulas Estructuradas:** Uso de algoritmos deterministas integrados (`FormulaEvaluator`):
  1. `ratio`: `(input_a / input_b) * scale`
  2. `difference`: `input_a - input_b`
  3. `percentage_gap`: `((input_a - input_b) / input_b) * 100`
  4. `direct`: `input_a`
  5. `sum`: `sum(inputs)`
  6. `average`: `avg(inputs)`

## Reglas de Evaluación de Estados (Targets & Direccionalidad)

### 1. Manejo de Target Ausente
- Si `target_value` es `NULL` / `None`, el estado asignado es estrictamente **`NO_TARGET`** con color **`gray`**.
- Nunca se fuerzan semáforos verdes o rojos ante la falta de una meta explícita.

### 2. Manejo de Datos Faltantes
- Si los datos de entrada son `NULL` o insuficientes, el estado asignado es **`NOT_AVAILABLE`** con color **`gray`**.
- El valor `0` NO representa datos faltantes; representa una cantidad nula real.

### 3. Direccionalidad `higher_is_better`
- `value >= target_value` ➔ **`ON_TARGET`** (Verde)
- `value < target_value` ➔ **`BELOW_TARGET`** (Rojo / Amarillo si se ubica en umbral de advertencia)

### 4. Direccionalidad `lower_is_better`
- `value <= target_value` ➔ **`ON_TARGET`** (Verde)
- `value > target_value` ➔ **`ABOVE_TARGET`** (Rojo / Amarillo)
