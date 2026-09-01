# 🏗️ FASE 02 — Arquitectura de Ingesta & Conservación RAW

## Flujo de Datos
```
  [ ARCHIVO FUENTE ] ──(Upload HTTP Multipart)──> [ POST /api/admin/imports/ ]
                                                            │
                                                            ▼
                                                ┌──────────────────────┐
                                                │ 1. Hash SHA-256      │
                                                │ 2. Check Idempotencia│
                                                └───────────┬──────────┘
                                                            │
                                                            ▼
                                                ┌──────────────────────┐
                                                │ 3. Storage RAW       │
                                                │ (uploads/raw/UUID.ext)│
                                                └───────────┬──────────┘
                                                            │
                                                            ▼
                                                ┌──────────────────────┐
                                                │ 4. Detector &        │
                                                │    Validator         │
                                                └───────────┬──────────┘
                                                            │
                                                            ▼
                                                ┌──────────────────────┐
                                                │ 5. DB ReportImport   │
                                                │ 6. AuditLog Event    │
                                                └──────────────────────┘
```

## Componentes Principales
1. **`app/models.py` (`ReportImport`):** Tabla relacional que guarda el registro inmutable de la carga, ruta RAW, SHA-256 hash, conteo de filas, warnings y errores.
2. **`app/services/hash_service.py`:** Genera SHA-256 Hex de 64 caracteres y verifica duplicidad por cliente.
3. **`app/services/file_storage_service.py`:** Garantiza almacenamiento inmutable en `uploads/raw/<uuid>.<ext>` filtrando extensiones peligrosas.
4. **`app/services/detector_service.py`:** Detecta delimitador, encoding, formato, headers y muestra de filas.
5. **`app/services/validator_service.py`:** Valida la estructura fila por fila garantizando CERO pérdida silenciosa de registros.
