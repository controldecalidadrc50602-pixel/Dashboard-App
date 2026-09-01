# 📑 FASE 04 — AUDITORÍA PREVIA E INSPECCIÓN TÉCNICA

**AGENTE / AUDITOR:** Kairos & Principal Software Architect  
**PROYECTO:** RC506 Reporting  
**FASE:** FASE 04 --- Motor KPI Dinámico, Configurable y Determinista  
**FECHA:** 2026-09-01  

---

## 1. Verificación del Estado Real del Código
- **Suite Pytest Acumulada:** Se ejecutó `pytest tests/ -v` arrojando **46/46 pruebas aprobadas (100% éxito)** en Fases 01, 02 y 03.
- **`KPIConfig` Existente (`app/models.py`):** Presente desde Fase 01 con relaciones hacia `Client`. Se preservará la retrocompatibilidad extendiendo sus campos sin romper migraciones ni datos existentes.
- **Parsers Botmaker:** `users`, `operatorsSessionsDebug`, `sessionStartingCauses` probados y operativos.
- **Parsers Yeastar a Incorporar:**
  - `YeastarExtensionStatsParser` ("Estadísticas de Llamadas de Extensión").
  - `YeastarExtensionActivityParser` ("Actividad Llamadas de Extensión").
  - `YeastarQueuePerformanceParser` ("Rendimiento de Cola").
  - `Yeastar AI Reports`: FUERA DE ALCANCE ACTUAL — DOCUMENTADO.

---

## 2. Requisitos de la Fase 04 a Construir
- **Separación Decoupled Nivel 5:** `RAW` ➔ `PARSER` ➔ `NORMALIZED` ➔ `BASE METRICS` ➔ `KPI ENGINE`.
- **Motor de Reglas y Fórmulas Seguro (Sin `eval()`):** Evaluador determinista con expresiones matemáticas explícitas (`ratio`, `difference`, `percentage_gap`, `linear_combination`).
- **Estados de KPI Deterministas:** `NO_DATA`, `NOT_AVAILABLE`, `NO_TARGET`, `ON_TARGET`, `BELOW_TARGET`, `ABOVE_TARGET`, `INVALID`.
  - *Regla Crítica:* Si un KPI no posee objetivo (`target=None`), su estado asignado es estrictamente `NO_TARGET` (nunca verde/rojo forzado).
- **Direccionalidad:** `higher_is_better`, `lower_is_better`, `range`.
- **Trazabilidad de Resultados (`KPIValue` / `KPIResult`):** Mantenimiento de historial por período y trazabilidad completa hasta el `import_id` y configuración utilizada.
- **Configuración Dinámica por Cliente:** Cero hardcoding de KPIs en código.

---

## 3. Plan de Implementación de la Fase 04
1. **Parsers Yeastar (`app/services/normalizer/`):** Implementar parsers para `Extension Statistics`, `Extension Call Activity` y `Call Center / Queue Performance`.
2. **Modelos ORM & Schemas (`app/models.py`, `app/schemas.py`):**
   - Extender `KPIConfig` con `identifier`, `formula_type`, `direction`, `unit`, `thresholds`, `metric_inputs`, `target`, `period_frequency`.
   - Crear entidad `KPIResult` para el almacenamiento del historial de valores calculados con trazabilidad.
3. **Motor de Fórmulas y Evaluación (`app/services/kpi_engine/`):**
   - `formula_evaluator.py`: Motor determinista sin `eval()`.
   - `kpi_service.py`: Cálculo, evaluación de targets y preservación de histórico.
4. **Endpoints API (`app/routers/kpis.py`):**
   - CRUD de configuraciones KPI por cliente (`GET`, `POST`, `PUT`, `DELETE`).
   - Cálculo y recálculo de KPIs (`POST /api/admin/kpis/calculate`).
   - Consulta de resultados e historial por cliente/período.
5. **Interfaz UI SPA (`templates/admin.html`):** Pestaña o sección de "Configuración y Motor de KPIs" por cliente.
6. **Suite Pytest (`tests/test_fase04.py`):** 20+ pruebas cubriendo formulas, targets, nulos, trazabilidad y Yeastar.
7. **Documentación (`documentacion/FASE_04/`):** 7+ documentos técnicos completos.
