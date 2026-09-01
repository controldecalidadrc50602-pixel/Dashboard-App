# 🔬 FASE 05 — Trazabilidad Completa (Fila RAW ➔ Insight)

## Cadena Criptográfica y Determinística
```
  [ Cliente ]
      │
      ▼
  [ ReportImport ] (storage_path: uploads/raw/UUID.ext, file_hash: SHA-256)
      │
      ▼
  [ NormalizedRecord ] (row_number, parser_version)
      │
      ▼
  [ KPIResult ] (valor evaluado, formula_used, input_values)
      │
      ▼
  [ AnalysisInsight ] (rule_id, severity, title, delta, trazabilidad completa)
```

## Respuesta Auditora
El endpoint `GET /api/admin/analysis/insights/{id}/traceability` reconstruye toda la evidencia en una sola respuesta JSON, permitiendo verificar de forma transparente qué fila del archivo RAW original produjo cada insight mostrado en el dashboard.
