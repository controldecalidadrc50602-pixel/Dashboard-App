# 🧹 FASE 03 — Políticas de Calidad de Datos

## Clasificación de Estado por Fila (`quality_status`)
- `VALID`: Parseo perfecto de la fila con todos los campos clave interpretados correctamente.
- `VALID_WITH_WARNINGS`: Registro procesado e insertado en `normalized_records`, pero con campos secundarios faltantes o discrepancias.
- `INVALID`: Registro con campos clave corruptos o ilegibles.

## Reglas de Limpieza y Conversión
1. **Representación de Vacíos:** Cadenas vacías `""`, `"N/A"`, `"-"`, `"null"` se convierten a `None` en Python y `NULL` en SQLite/SQL.
2. **Sin Infección de Ceros (No Zero-Padding):** Un conteo o duración ausente NO se rellena con `0`. Permanece `NULL` para evitar que afecte promedios o genere métricas engañosas.
3. **No Suponer Fechas Acuales:** Si una fecha no se puede interpretar, permanece como `NULL` en lugar de asignarle la hora actual (`datetime.now()`).
