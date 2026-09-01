# 📑 FASE 02 — Validación Estructural y No Pérdida de Datos

## Principio Fundamental
**CERO PÉRDIDA SILENCIOSA DE DATOS**

Si una fila presenta valores sospechosos o incongruentes en el número de columnas:
- La fila NO se descarta.
- Se registra en el arreglo `warnings` o `errors` de la entidad `ReportImport`:
  ```json
  {
    "row": 154,
    "field": "column_count",
    "message": "Discrepancia en número de columnas (esperadas 8, encontradas 7)",
    "severity": "WARNING"
  }
  ```

## Estados de Validación de Importación
- `RECEIVED`: Archivo recibido y hash calculado.
- `VALIDATING`: Procesando detección y estructura.
- `VALID`: Estructura perfecta sin discrepancias.
- `VALID_WITH_WARNINGS`: Archivo procesable pero contiene filas o encabezados con advertencias.
- `INVALID`: Archivo vacío, ilegible o corrupto.
- `DUPLICATE`: Archivo con SHA-256 previamente registrado para el cliente.
