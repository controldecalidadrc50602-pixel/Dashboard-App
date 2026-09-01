# 🔬 FASE 04 — Trazabilidad del Resultado KPI

## Cadena de Trazabilidad Completa
```
  [ Cliente ]
      │
      ▼
  [ KPIConfig ] (Regla, Meta, Fórmula, Dirección, Versión)
      │
      ▼
  [ ReportImport ] (SHA-256, storage_path RAW)
      │
      ▼
  [ NormalizedRecord ] (row_number, parser_version)
      │
      ▼
  [ KPIResult ] (Valor Calculado, Estado, Valores de Entrada, Metadata de Trazabilidad)
```

## Respuesta Auditora
Cada evaluación producida por el motor permite responder de forma exacta:  
**¿De dónde proviene este resultado (ej. SLA 84.02%) y con qué fórmula y archivo fue generado?**

El endpoint `GET /api/admin/kpis/results/{id}/traceability` retorna:
- `result_id`: Identificador del resultado.
- `client_name`: Cliente evaluado.
- `period`: Período de evaluación (YYYY-MM).
- `kpi_code`: Código único del indicador.
- `formula_used`: Fórmula exacta aplicada.
- `input_values`: Valores numéricos de entrada utilizados en la fórmula.
- `traceability_info`: Referencia directa al `import_id`, `source_code`, `report_type` y versión de la configuración.
