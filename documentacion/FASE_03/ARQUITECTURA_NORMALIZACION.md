# 🏗️ FASE 03 — Arquitectura de Normalización & Capa de Métricas Base

## Pipeline de Procesamiento Decoupled
```
  [ ARCHIVO RAW ] ──> [ ReportImport ]
                           │
                           ▼
                  ┌─────────────────┐
                  │ Select Parser   │ ──> (BotmakerUsers, BotmakerOperators, BotmakerSessions, Generic)
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  BaseParser     │ ──> Clean String / Datetime / Duration / Int / Bool (Nulos explícitos)
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ NormalizedRecord│ ──> Almacenamiento en BD (client_id, import_id, row_number, parser_version)
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Base Metrics    │ ──> Cálculo de métricas operativas (sesiones, atención, tiempos, abandono)
                  └─────────────────┘
```

## Principios de Diseño Aplicados
1. **Separación de Capas Nivel 4:** RAW (Inmutable) ➔ NORMALIZED (Eliminable/Reprocesable) ➔ METRICS (Calculadas dinámicamente).
2. **Versionado de Parsers:** Seguimiento explícito de la versión del parser utilizada para cada registro normalizado (ej. `botmaker-users-v1.0`).
3. **Reprocesabilidad Atómica:** Ejecutar `POST /api/admin/imports/{id}/process` purga los `NormalizedRecords` previos del `import_id` y los reconstruye sin tocar el archivo RAW almacenado en disco.
