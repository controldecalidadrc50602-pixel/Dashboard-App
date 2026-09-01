# 📜 05. Historial de Cambios y Planes Futuros

## 📋 Registro de Cambios Realizados (Changelog)

### Versión 1.7.0 (2026-09-01) - FASE 05: Motor de Análisis Determinístico RC506 y Capa de Insights Ejecutivos
- **Capa Semántica & Motor de Análisis RC506:** Transformación determinística de KPIs evaluados en observaciones e insights explicables sin IA ni causalidad falsa.
- **Catálogo Declarativo de Reglas:** Reglas declarativas para metas, comparativas MoM, tendencias históricas en 3+ períodos y calidad de datos.
- **Entidad `AnalysisInsight`:** Persistencia relacional de observaciones con deltas absolutos/porcentuales y severidades (`INFO`, `POSITIVE`, `WARNING`, `CRITICAL`, `NOT_AVAILABLE`).
- **Cadena Completa de Trazabilidad:** Inspección desde la observación hasta la fila del archivo RAW de origen.
- **Pruebas Automatizadas:** **83/83 pruebas unitarias e integración en Pytest aprobadas al 100%**.

### Versión 1.6.0 (2026-09-01) - FASE 04: Motor KPI Dinámico, Configurable y Determinista

- **Motor KPI Multicliente Desacoplado:** Definición dinámica de KPIs, objetivos, unidades y reglas por cliente sin hardcoding.
- **Evaluador Determinista sin `eval()`:** `FormulaEvaluator` algebraico seguro con división por cero tolerante.
- **Parsers Yeastar Muestras Reales:** Implementados `YeastarExtensionStatsParser`, `YeastarExtensionActivityParser` y `YeastarQueuePerformanceParser`.
- **Yeastar AI Reports:** Clasificado formalmente como "FUERA DE ALCANCE ACTUAL — NO UTILIZADO".
- **Regla Estricta de Targets:** Ante falta de objetivo configurado, el estado retornado es `NO_TARGET` (nunca verde/rojo forzado).
- **Trazabilidad & Histórico:** Tabla `kpi_results` preservando evolutivos con auditoría hasta el archivo RAW.
- **Pruebas Automatizadas:** **66/66 pruebas unitarias e integración en Pytest aprobadas al 100%**.

### Versión 1.5.0 (2026-09-01) - FASE 03: Normalización de Datos y Capa de Métricas Base

- **Separación de Capas (RAW / NORMALIZED / METRICS):** Estructura en `normalized_records` derivada e inmutable sin tocar el archivo RAW almacenado en disco.
- **Parsers Botmaker v1.0:** Implementados `BotmakerUsersParser`, `BotmakerOperatorsParser` y `BotmakerSessionsParser`.
- **Diferenciación de NULL vs 0:** Prohibición de ceros falsos o timestamps automáticos en campos faltantes.
- **Trazabilidad Absoluta Fila ➔ RAW:** Seguimiento directo de `row_number`, `import_id` y `parser_version`.
- **Métricas Operativas Base:** Cálculo desacoplado de sesiones, mensajes, atenciones, tiempo promedio de espera, duración y tasa de abandono.
- **Reprocesabilidad Atómica:** Endpoint `POST /api/admin/imports/{id}/process` purga e inserta registros de forma transparente.
- **Pruebas Automatizadas:** **46/46 pruebas unitarias e integración en Pytest aprobadas al 100%**.

### Versión 1.4.0 (2026-09-01) - FASE 02: Ingesta Autónoma y Conservación de Fuentes

- **Almacenamiento Inmutable RAW:** Conservación de archivos fuente originales identificados internamente por UUID en `uploads/raw/`.
- **Identificación SHA-256 e Idempotencia:** Prevención de cargas duplicadas mediante cálculo de hash de 64 caracteres.
- **Validación Estructural y No Pérdida Silenciosa:** Inspección de delimitadores, encodings, encabezados y validación fila por fila con registro de advertencias y errores.
- **Formatos Botmaker & Yeastar:** Manejo nativo de reportes `users`, `operatorsSessionsDebug`, `sessionStartingCauses` e ingesta genérica para Yeastar (`NO VERIFICADO — REQUIERE ARCHIVO DE MUESTRA`).
- **Interfaz SPA de Ingesta & Modal Preview:** Pestaña "Ingesta de Archivos", modal de inspección RAW y tabla de historial con badges de estado.
- **Pruebas Automatizadas:** 28/28 pruebas en Pytest (100% aprobadas).

### Versión 1.3.0 (2026-09-01) - FASE 01: Arquitectura Multi-Cliente & Dashboard Global RC506
- **Dashboard Global RC506 (`GET /api/admin/dashboard-global`):** Consolidado ejecutivo con estados por cliente, alertas preliminares y métricas agregadas comparables.
- **Trazabilidad y Auditoría Persistente (`app/audit.py`):** Registro de eventos administrativos y de ingesta en `audit_logs`.

### Versión 1.2.0 - Sistema Multi-KPI Adaptativo

- **Módulos KPI dinámicos:** Implementación de la columna `kpi_modules` en clientes y `extra_data` en reportes.
- **Cliente Petopia integrado:** Adición del cliente Petopia con métricas Yeastar (Agentes) y Botmaker (Bot).
- **Rediseño del Dashboard Admin:** Las tarjetas y gráficos del dashboard se adaptan al cliente activo.
- **Rediseño de Diapositivas (Slides):** Las diapositivas ajustan su contenido automáticamente según las métricas del cliente.
- **Rediseño de Vistas Públicas:** Adaptación completa del frontend del cliente final según sus módulos habilitados.

### Versión 1.1.0 - Corrección de Compatibilidad y Túneles
- **Compatibilidad Python 3.13:** Actualización de SQLAlchemy a la versión `2.0.36` (solución del bug `FastIntFlag`).
- **DevTunnels / Redes:** Adición de cabeceras anti-CSRF (`X-Tunnel-Skip-AntiCSRF`), timeouts y manejo de errores `try/catch` en el formulario de login.

### Versión 1.0.0 - Lanzamiento Inicial
- Estructura Backend FastAPI con base de datos SQLite y ORM SQLAlchemy.
- Autenticación JWT y Hashing bcrypt.
- Frontend SPA completo en HTML5 / Glassmorphic CSS.

---

## 🔮 Planes Futuros y Mejoras Propuestas

1. **Exportación a PDF / Excel:** Botón para descargar el reporte mensual o la vista de slides en formato PDF o Excel.
2. **Plantillas Preconfiguradas (Presets):** Selector de un clic al crear cliente ("Plantilla Clínica", "Plantilla Call Center", "Plantilla E-Commerce").
3. **Múltiples Usuarios Admin:** Soporte para varios ejecutivos de cuenta con permisos diferenciados.
4. **Integración Directa por API/Webhooks:** Conexión directa con APIs de Yeastar y Botmaker para automatizar la carga mensual.
