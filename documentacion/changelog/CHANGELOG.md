# 📜 CHANGELOG — RC506 Reporting

Todos los cambios notables realizados en este proyecto serán documentados en este archivo.

## [FASE 00] - 2026-09-01
### Añadido
- Auditoría técnica completa del sistema y establecimiento de la línea base.
- Creación de la estructura de documentación en `/documentacion/` y `/documentacion/fases/`.
- Informe oficial de FASE 00 (`FASE_00_AUDITORIA.md`) con evaluación de madurez, seguridad, brechas y arquitectura.
- Plan maestro para FASE 01 (Arquitectura Multi-Cliente & Dashboard Global RC506).

## [FASE 01] - 2026-09-01
### Añadido
- **Endpoint Dashboard Global RC506 (`GET /api/admin/dashboard-global`):** Consolidado ejecutivo con estados por cliente, alertas preliminares, métricas agregadas comparables y log de auditoría.
- **Trazabilidad y Auditoría Persistente (`app/audit.py`):** Servicio de auditoría para registrar eventos en `audit_logs`.
- **Nuevos Esquemas Pydantic (`app/schemas.py`):** Modelos de validación para `SourceOut`, `KPIConfigOut`, `AuditLogOut`, `ClientStatusOut`, `GlobalMetricsOut` y `DashboardGlobalResponse`.
- **Frontend Admin SPA (`templates/admin.html`):** Integración del **Dashboard Global RC506** como pantalla de inicio del panel administrativo con navegación fluida al Dashboard Individual por cliente.
- **Suite de Pruebas Automatizadas (`tests/test_fase01.py`):** 13 escenarios de prueba automatizados con Pytest alcanzando 100% de tasa de éxito.
- **Documentación Completa de Fase 01:**
  - `documentacion/fases/FASE_01_MULTI_CLIENTE.md`
  - `documentacion/02_ARQUITECTURA.md`
  - `documentacion/03_MODELO_DATOS.md`
  - `documentacion/10_DASHBOARD_GLOBAL.md`
  - `documentacion/14_SEGURIDAD.md`
  - `documentacion/16_PRUEBAS.md`

### Modificado
- `app/main.py`: Inclusión del router `dashboard_global`.
- `app/auth.py`: Refuerzo de seguridad JWT e inspección de `SECRET_KEY`.
- `app/routers/auth.py`, `clients.py`, `reports.py`, `public.py`: Integración de auditoría en operaciones clave.

## [FASE 05] - 2026-09-01
### Añadido
- **Motor de Análisis Determinístico RC506 (`app/services/analysis_engine/`):** Transformación de resultados KPI en observaciones explicables sin IA, LLMs ni causalidad falsa.
- **Catálogo Declarativo de Reglas (`rules_registry.py`):** Reglas declarativas para `TARGET_COMPLIANCE`, `PERIOD_OVER_PERIOD`, `TREND`, `THRESHOLD_VARIATION`, `CONCENTRATION` y `DATA_QUALITY`.
- **Modelo ORM `AnalysisInsight` (`app/models.py`):** Entidad relacional para la persistencia e idempotencia de observaciones e insights por cliente y período.
- **Endpoints de Análisis & Insights (`app/routers/analysis.py`):** Endpoints `/run`, `/clients/{id}/insights`, `/rules`, `/traceability`.
- **Interfaz UI SPA Actualizada (`templates/admin.html`):** Sección "Análisis RC506", filtros por severidad (`CRITICAL`, `WARNING`, `POSITIVE`, `INFO`, `NOT_AVAILABLE`), tarjetas ejecutivas y modal de evidencia de origen.
- **Suite de Pruebas Automatizadas (`tests/test_fase05.py`):** 17 nuevos casos de prueba alcanzando **83/83 pruebas totales aprobadas (100%)**.
- **Documentación Completa de Fase 05 (`documentacion/FASE_05/`):** 8 documentos técnicos.

## [FASE 04] - 2026-09-01

### Añadido
- **Motor KPI Dinámico & Configurable (`app/services/kpi_engine/`):** Configuración de KPIs independientes por cliente sin código hardcodeado.
- **Evaluador de Fórmulas Deterministas sin `eval()` (`formula_evaluator.py`):** Algoritmos para `ratio`, `difference`, `percentage_gap`, `direct`, `sum`, `average` con división por cero segura.
- **Evaluador de Estados & Direccionalidad:** Asignación de estados (`NO_DATA`, `NOT_AVAILABLE`, `NO_TARGET`, `ON_TARGET`, `BELOW_TARGET`, `ABOVE_TARGET`). Regla estricta: Sin target ➔ `NO_TARGET` (gris).
- **Parsers Yeastar Muestras Reales (`app/services/normalizer/yeastar_parsers.py`):**
  - `YeastarExtensionStatsParser` (`yeastar-ext-stats-v1.0`)
  - `YeastarExtensionActivityParser` (`yeastar-ext-activity-v1.0`)
  - `YeastarQueuePerformanceParser` (`yeastar-queue-perf-v1.0`)
- **Yeastar AI Reports:** Documentado explícitamente como "FUERA DE ALCANCE ACTUAL — NO UTILIZADO".
- **Modelo de Resultados & Histórico (`app/models.py`, `KPIResult`):** Almacenamiento persistente de evaluaciones por cliente y período con trazabilidad hasta el archivo RAW.
- **Endpoints de Motor KPI (`app/routers/kpis.py`):** CRUD de KPIs por cliente, `/calculate`, `/results`, `/results/{id}/traceability`.
- **Interfaz UI SPA Actualizada (`templates/admin.html`):** Sección "Motor de KPIs", formulario de regla/meta por cliente, tabla de resultados evaluados y modal de trazabilidad.
- **Suite de Pruebas Automatizadas (`tests/test_fase04.py`):** 20 nuevos casos de prueba automatizados alcanzando **66/66 pruebas totales aprobadas (100%)**.
- **Documentación Completa de Fase 04 (`documentacion/FASE_04/`):** 7 documentos técnicos.

## [FASE 03] - 2026-09-01

### Añadido
- **Capa de Normalización & Modelo ORM (`app/models.py`, `NormalizedRecord`):** Estructura relacional desacoplada en 4 niveles (RAW ➔ PARSER ➔ NORMALIZED ➔ METRICS).
- **Parsers Botmaker Específicos (`app/services/normalizer/`):**
  - `BotmakerUsersParser` (`botmaker-users-v1.0`)
  - `BotmakerOperatorsParser` (`botmaker-operators-v1.0`)
  - `BotmakerSessionsParser` (`botmaker-sessions-v1.0`)
- **Gestión Estricta de Nulos y Nula Infección de Ceros:** Campos faltantes o vacíos almacenados como `NULL` en SQL y `None` en Python (prohibición de ceros o falsos por defecto).
- **Calculador de Métricas Operativas Base (`app/services/normalizer/metrics_calculator_service.py`):** Métricas derivadas de sesiones, mensajes, atenciones, esperas y abandono con documentación formal de fórmulas.
- **Trazabilidad por Fila & Reprocesabilidad Inmutable:** Vinculación directa de cada registro normalizado a su `row_number` de origen y versión del parser (`parser_version`). Reprocesamiento de RAWs mediante `POST /api/admin/imports/{id}/process`.
- **Endpoints de Normalización, Métricas & Calidad:** `/process`, `/normalized-summary`, `/quality`.
- **Interfaz UI SPA Actualizada (`templates/admin.html`):** Botón de normalización/reprocesamiento, modal de métricas base, versión de parser y trazabilidad por fila.
- **Suite de Pruebas Automatizadas (`tests/test_fase03.py`):** 18 nuevos casos de prueba automatizados alcanzando **46/46 pruebas totales aprobadas (100%)**.
- **Documentación Completa de Fase 03 (`documentacion/FASE_03/`):** 10 documentos técnicos.

## [FASE 02] - 2026-09-01

### Añadido
- **Almacenamiento Inmutable RAW (`uploads/raw/`):** Conservación de archivos fuente originales identificados internamente por UUID para prevenir Path Traversal.
- **Trazabilidad e Idempotencia SHA-256 (`app/services/hash_service.py`):** Detección de archivos duplicados evitando la re-ingesta accidental.
- **Detección y Validación de Estructura (`app/services/detector_service.py` y `validator_service.py`):** Identificación automática de delimitadores, encodings y validación fila por fila garantizando CERO pérdida silenciosa de registros.
- **Entidad ORM y Router API (`app/models.py`, `app/routers/imports.py`):** Modelo `ReportImport` y endpoints `POST /api/admin/imports`, `GET /api/admin/imports`, `GET /api/admin/imports/{id}` y `GET /api/admin/imports/{id}/preview`.
- **Interfaz SPA de Ingesta & Modal Preview (`templates/admin.html`):** Pestaña "Ingesta de Archivos", modal de inspección RAW y tabla de historial con badges de estado.
- **Suite de Pruebas Automatizadas (`tests/test_fase02.py`):** 15 nuevos casos de prueba automatizados en Pytest (28/28 pruebas totales aprobadas al 100%).
- **Documentación de Fase 02:**
  - `documentacion/FASE_02/AUDITORIA_PREVIA.md`
  - `documentacion/FASE_02/ARQUITECTURA_INGESTA.md`
  - `documentacion/FASE_02/FORMATOS_BOTMAKER.md`
  - `documentacion/FASE_02/FORMATOS_YEASTAR.md`
  - `documentacion/FASE_02/VALIDACION_ARCHIVOS.md`
  - `documentacion/FASE_02/SEGURIDAD_ARCHIVOS.md`
  - `documentacion/FASE_02/TESTS_FASE_02.md`
  - `documentacion/FASE_02/INFORME_FINAL_FASE_02.md`

### Preservado
- Integridad total del Dashboard Global RC506, Dashboard Individual por cliente, clientes Kidoz y Petopia, reportes mensuales, slides y links públicos.



