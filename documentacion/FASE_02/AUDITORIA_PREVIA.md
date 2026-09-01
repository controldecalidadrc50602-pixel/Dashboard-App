# 📑 FASE 02 — AUDITORÍA PREVIA E INSPECCIÓN TÉCNICA

**AGENTE / AUDITOR:** Kairos & Principal Software Architect  
**PROYECTO:** RC506 Reporting  
**FASE:** FASE 02 --- Ingesta Autónoma y Conservación de Fuentes  
**FECHA:** 2026-09-01  

---

## 1. Arquitectura Actual (Línea Base Post-Fase 01)
- **Backend:** FastAPI + SQLAlchemy 2.0 + SQLite local (`dashboard.db`).
- **Autenticación:** JWT HTTP Bearer con dependencia `get_current_admin`.
- **Auditoría:** Servicio `log_audit_action` registrando eventos en `audit_logs`.
- **Endpoints Existentes:** `/api/auth/login`, `/api/clients`, `/api/clients/{id}/reports`, `/api/admin/dashboard-global`, `/slides/{id}`, `/api/public/{token}`.
- **Frontend:** SPA basada en Jinja2/Vanilla JS en `templates/admin.html`.

---

## 2. Puntos Reutilizables
- **Control de Acceso:** Uso directo de `get_current_admin` para asegurar endpoints de ingesta.
- **Auditoría Persistente:** Reutilización de `log_audit_action` para registrar eventos de ingesta (`IMPORT_STARTED`, `IMPORT_VALIDATED`, `IMPORT_COMPLETED`, `IMPORT_FAILED`, `IMPORT_DUPLICATE`, `RAW_FILE_ACCESSED`).
- **Esquema Multi-Cliente:** Relación directa entre la nueva entidad `ReportImport` y los clientes existentes en `clients`.
- **Fuentes Existentes:** Uso de la tabla `sources` (`botmaker`, `yeastar`, `manual`).

---

## 3. Puntos que Requieren Extensión
- **Modelo ORM (`app/models.py`):** Creación de la entidad `ReportImport` para la persistencia inmutable de metadata de cargas.
- **Capas de Servicio (`app/services/`):**
  - `hash_service.py`: Cálculo SHA-256 e idempotencia.
  - `file_storage_service.py`: Conservación inmutable de archivos RAW en `uploads/raw/`.
  - `detector_service.py`: Identificación de delimitadores, encodings y formatos (TSV, CSV, XLSX, TXT).
  - `validator_service.py`: Validación por fila y detección de errores sin pérdida silenciosa.
- **Endpoints de Ingesta (`app/routers/imports.py`):** Creación de `POST /api/admin/imports`, `GET /api/admin/imports`, `GET /api/admin/imports/{id}` y `GET /api/admin/imports/{id}/preview`.
- **Interface SPA (`templates/admin.html`):** Añadir sección "Ingesta de Archivos", modal de preview e historial de cargas.

---

## 4. Archivos Fuente y Formatos Encontrados

### Botmaker
- **Estructura Requerida:** Archivos TSV (`.tsv`).
  - `users`: `users-YYYY.MM.DD-HH.MM.tsv` (conversación, sesión, canal, contacto, mensajes, etc.).
  - `operatorsSessionsDebug`: `operatorsSessionsDebug-YYYY.MM.DD-HH.MM.tsv` (sesiones, agentes, colas, tiempos, enlaces).
  - `sessionStartingCauses`: `sessionStartingCauses-YYYY.MM.DD-HH.MM.tsv` (usuario, canal, notificaciones, timestamps).
- **Formatos:** TSV / UTF-8 / Tab-delimited.

### Yeastar
- **Estructura Requerida:** Familias `Extension`, `Call Center`, `Call Activity`, `AI Reports`.
- **Estado de Muestra:** `NO VERIFICADO — REQUIERE ARCHIVO DE MUESTRA`. No existen archivos de ejemplo reales cargados en la raíz del repositorio. Se implementa validación genérica flexible sin inventar campos ficticios.

---

## 5. Riesgos Identificados
- **Riesgo de Inyección / Traversal:** Intento de usar nombres originales de archivo en el sistema de archivos (Mitigación: almacenamiento con UUID/Hash interno).
- **Riesgo de Duplicidad Silenciosa:** Re-subir el mismo archivo causando duplicación (Mitigación: Hash SHA-256 idempotente).
- **Riesgo de Pérdida Silenciosa:** Omisión de filas malformadas (Mitigación: Registro explícito de errores y warnings por número de fila).

---

## 6. Plan de Implementación Incremental
1. Crear carpeta de almacenamiento inmutable `uploads/raw/`.
2. Actualizar `app/models.py` y `app/schemas.py` con `ReportImport`.
3. Crear servicios `hash_service`, `file_storage_service`, `detector_service` y `validator_service`.
4. Crear router `app/routers/imports.py` y registrarlo en `app/main.py`.
5. Extender `templates/admin.html` con la interfaz de carga, preview e historial de ingesta.
6. Desarrollar suite pytest `tests/test_fase02.py` (15 casos).
7. Generar suite completa de documentación en `documentacion/FASE_02/`.
