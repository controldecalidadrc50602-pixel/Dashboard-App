# 📑 FASE 03 — AUDITORÍA PREVIA E INSPECCIÓN TÉCNICA

**AGENTE / AUDITOR:** Kairos & Principal Software Architect  
**PROYECTO:** RC506 Reporting  
**FASE:** FASE 03 --- Normalización de Datos y Capa de Métricas Base  
**FECHA:** 2026-09-01  

---

## 1. Verificación del Estado Real del Código (Fases 01 y 02)
- **Suite Pytest:** Se ejecutó `pytest tests/ -v` arrojando un resultado comprobado de **28/28 pruebas aprobadas (100% exito)**.
- **Entidad `ReportImport` (`app/models.py`):** Presente y operativa con campos de metadata, hash SHA-256, storage_path, warnings y errors.
- **Almacenamiento RAW (`uploads/raw/`):** Operativo con conservación inmutable en archivos nombrados mediante UUIDs.
- **Idempotencia SHA-256 (`app/services/hash_service.py`):** Generación de hashes de 64 caracteres e inspección de duplicados.
- **Detector & Validador (`app/services/detector_service.py`, `validator_service.py`):** Identificación precisa de encodings y delimitadores con inspección fila por fila sin descarte silencioso de datos.
- **Router API (`app/routers/imports.py`):** Endpoints activos con control de acceso JWT y auditoría de eventos.
- **UI Admin SPA (`templates/admin.html`):** Pestaña "Ingesta de Archivos", vista previa modal e historial interactivo.

---

## 2. Requisitos de FASE 03 a Construir
- **Separación Estricta Nivel 4 (RAW / NORMALIZED / METRICS):**
  - **RAW:** Archivo fuente inmutable (conservado en disco).
  - **NORMALIZED:** Representación estructurada derivada almacenada en tabla `normalized_records`.
  - **METRICS:** Métricas operativas base agregables y recalculables.
- **Parsers Botmaker Específicos:**
  - Parser `users`: conversaciones, fecha/hora, canales, contactos, mensajes.
  - Parser `operatorsSessionsDebug`: sesiones, agentes, colas, tiempos de espera/atención, enlaces.
  - Parser `sessionStartingCauses`: inicio de sesión, canales, notificaciones, timestamps de entrega/lectura.
- **Catalogación Yeastar:** Permanece como `NO VERIFICADO — REQUIERE ARCHIVO DE MUESTRA` preparando la arquitectura modular para adaptadores futuros.
- **Trazabilidad Absoluta:** Vinculación de cada registro normalizado a `client_id`, `import_id`, `storage_path` y `row_number` original.
- **Diferenciación Estricta `NULL / NOT_AVAILABLE` vs `0`:** Los campos no presentes en una fuente se almacenan como `NULL` o `NOT_AVAILABLE` para evitar métricas o KPIs sesgados.
- **Reprocesamiento & Versionado:** Reprocesamiento de cualquier `ReportImport` mediante versión declarada del parser (ej. `botmaker-users-v1.0`).

---

## 3. Plan de Implementación de la Fase 03
1. **Modelos ORM (`app/models.py`):** Añadir entidad `NormalizedRecord` con JSON payload de trazabilidad y campos de auditoría.
2. **Servicios de Normalización & Parsers (`app/services/normalizer/`):**
   - `base_parser.py`: Clase base abstracta.
   - `botmaker_users_parser.py`: Parser para `users-*.tsv`.
   - `botmaker_operators_parser.py`: Parser para `operatorsSessionsDebug-*.tsv`.
   - `botmaker_sessions_parser.py`: Parser para `sessionStartingCauses-*.tsv`.
   - `metrics_calculator_service.py`: Cálculo de métricas operativas base.
3. **Endpoints API (`app/routers/imports.py`):**
   - `POST /api/admin/imports/{id}/process`: Iniciar normalización / reprocesamiento.
   - `GET /api/admin/imports/{id}/normalized-summary`: Resumen de registros normalizados y métricas base.
   - `GET /api/admin/imports/{id}/quality`: Métricas de calidad y trazabilidad.
4. **Interfaz UI SPA (`templates/admin.html`):** Botón de "Normalizar / Reprocesar" y modal de Resumen Normalizado & Calidad de Datos.
5. **Suite Pytest (`tests/test_fase03.py`):** 16+ casos de prueba cubriendo parsing, trazabilidad, NULLs, reprocesamiento y compatibilidad.
6. **Documentación (`documentacion/FASE_03/`):** 10 documentos técnicos completos.
