# 📈 FASE 05 — Comparabilidad y Evaluación de Tendencias

## Reglas de Comparabilidad Estricta
Para comparar dos evaluaciones entre distintos períodos:
1. Pertenecer al mismo `client_id`.
2. Compartir el mismo `kpi_config_id` o `kpi_code`.
3. Tener la misma unidad de medida y fórmula.
4. Si la versión de la regla cambió (`version`), se registra la anotación de discrepancia sin fabricar deltas engañosos.

## Umbral Mínimo para Tendencias
- **Requisito:** Mínimo 3 períodos evaluables con datos numéricos válidos.
- **Sin datos suficientes:** Si existen < 3 períodos, no se inventa una tendencia; se marca formalmente como `insufficient_data`.
