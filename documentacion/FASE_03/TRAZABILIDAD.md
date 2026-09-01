# 🔬 FASE 03 — Trazabilidad de Origen (Fila RAW ➔ NormalizedRecord)

## Cadena de Trazabilidad Criptográfica y Física
```
  [ Cliente ]
      │
      ▼
  [ ReportImport ] (file_hash SHA-256, storage_path: uploads/raw/UUID.ext)
      │
      ▼
  [ NormalizedRecord ] (row_number, parser_version, raw_data JSON)
```

## Garantías de Trazabilidad
Cada registro en `normalized_records` responde a la pregunta auditora:  
**¿De qué archivo y número de fila exacto provino este dato?**

- `import_id`: Referencia unívoca a la importación y su archivo RAW inmutable en disco.
- `row_number`: Número de fila exacto en el archivo original (1-indexed, comenzando en fila 2 para datos).
- `raw_data`: Copia íntegra de la fila cruda recibida en el momento de la carga.
- `parser_version`: Versión exacta de la regla/parser que interpretó la fila.
