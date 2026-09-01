# 📊 00. Estado Actual del Sistema (Línea Base)

**Fecha de Auditoría:** 01 de Septiembre, 2026  
**Auditor / Arquitecto:** Principal Software Engineer & Solution Architect  
**Fase:** FASE 00 — Auditoría y Línea Base  

---

## 1. Estado Real

El proyecto es un prototipo funcional basado en **FastAPI (Python 3.13)** en el backend y **HTML/Vanilla JS/Chart.js** en el frontend.
Actualmente cuenta con almacenamiento en **SQLite (`dashboard.db`)** administrado a través de **SQLAlchemy 2.0 ORM**.

- **Clientes registrados en DB:** 2 clientes (`Kidoz` con ID=1 y `Petopia` con ID=2).
- **Reportes cargados:**
  - `Kidoz`: 8 reportes mensuales (Enero – Agosto 2026).
  - `Petopia`: 4 reportes mensuales (Mayo – Agosto 2026).
- **Métricas:** Los reportes almacenan KPIs rígidos de Chat, Ventas, Citas, Soporte, Llamadas y Calidad Kidoz, además de una columna `extra_data` JSON básica donde se guardan contadores agregados de Yeastar y Botmaker.

---

## 2. Arquitectura Real

```
[ Frontend: HTML5 / Glassmorphic CSS / Vanilla JS / Chart.js ]
                             │
                             ▼ (HTTP Fetch API + JWT Bearer)
[ Backend: FastAPI (Python 3.13) + Pydantic V2 ]
                             │
                             ▼ (SQLAlchemy 2.0 ORM)
[ Base de Datos: SQLite (dashboard.db) ]
```

### Componentes Principales:
- `run.py`: Script de arranque Uvicorn.
- `app/database.py`: Conexión SQLite y manejo de sesión SQLAlchemy.
- `app/models.py`: 3 Modelos ORM (`Client`, `MonthlyReport`, `PublicView`).
- `app/schemas.py`: Schemas de validación Pydantic V2.
- `app/auth.py`: Utilidades JWT (`jose`) y hashing de clave (`bcrypt`).
- `app/routers/`:
  - `auth.py`: Endpoint `/api/auth/login`.
  - `clients.py`: CRUD `/api/clients/`.
  - `reports.py`: CRUD `/api/clients/{id}/reports/`.
  - `public.py`: Enlaces públicos `/api/public/{token}`.
- `templates/`:
  - `login.html`: Pantalla de autenticación admin.
  - `admin.html`: SPA con sidebar (Dashboard, Clientes, Reportes, Links).
  - `slides.html`: Presentación en diapositivas para reuniones.
  - `public.html`: Vista de consulta para clientes finales.

---

## 3. Funcionalidades Existentes

- [x] Autenticación JWT básica con usuario/contraseña de administrador desde `.env`.
- [x] CRUD completo de Clientes (Nombre, Descripción, Color, Avatar).
- [x] Asignación preliminar de banderas de módulos en el cliente (`kpi_modules` como lista de strings en JSON).
- [x] CRUD de Reportes Mensuales con entrada manual de datos mediante formulario modal.
- [x] Cálculo de Tasa de Cierre en servidor (`sales / leads * 100`).
- [x] Visualización de Presentación Ejecutiva (`slides.html`) con navegación por teclado y modo pantalla completa.
- [x] Generación de Enlaces Públicos por Token UUID con opciones de contraseña hash y expiración.
- [x] Formulario modal de reporte que oculta/muestra secciones según la lista `kpi_modules` del cliente.

---

## 4. Funcionalidades Faltantes (Brechas Críticas)

- [ ] **Importación Autónoma de Archivos:** No existe motor de carga o ingesta de archivos Excel/CSV exportados por Botmaker o Yeastar. Todo el ingreso de datos es manual.
- [ ] **Dashboard Global Multicliente RC506:** El dashboard actual se limita a mostrar los datos de **UN SOLO cliente a la vez** (el seleccionado en el dropdown). No existe la vista consolidada ejecutiva de RC506 para monitorear el estado de los 30+ clientes.
- [ ] **Normalización de Métricas & Motor de KPIs:** Los KPIs están acoplados directamente a columnas fijas de la tabla `monthly_reports`. No existe una entidad independiente `KPI`, `METRIC` ni `KPI_CONFIGURATION`.
- [ ] **Capa de Análisis Determinístico:** No existe un motor que calcule variaciones, tendencias, alertas automáticas, hallazgos o recomendaciones. El sistema solo despliega valores numéricos crudos.
- [ ] **Persistencia de Archivos Crudos (RAW File Storage):** No se guardan los archivos originales ni los registros fuente (`RAW_FILE`, `RAW_RECORD`).
- [ ] **Logs de Auditoría de Trazabilidad (`AUDIT_LOG`):** No se registra quién importa datos, cuándo ni qué cambios realiza.
- [ ] **Aislamiento y Autorización por Recursos:** Las llamadas públicas no tienen control de tasa (Rate Limiting) y las llamadas admin confían en un único rol global de admin.

---

## 5. Deuda Técnica

1. **Esquema de BD Rígido:** La tabla `monthly_reports` contiene 20+ columnas fijas escritas específicamente para el caso inicial Kidoz. Se utiliza `extra_data` (JSON) como parche temporal.
2. **Ausencia de Pipeline de Ingesta:** No existen parsers de pandas/openpyxl para procesar reportes reales de Yeastar (Extension, Call Center, Activity, AI) ni de Botmaker (users, operatorsSessionsDebug, sessionStartingCauses).
3. **Monolito de Script Frontend:** El JS del panel admin (`admin.html`) está embebido directamente en la plantilla Jinja2 en lugar de módulos JS estructurados.
4. **Falta de Pruebas Automatizadas:** No existen pruebas unitarias o de integración (`pytest`) en la suite actual.

---

## 6. Seguridad Actual

- **Puntaje de Seguridad Actual:** `4.5 / 10`
- **Fortalezas:**
  - Contraseñas procesadas con `bcrypt`.
  - Tokens JWT generados con exp de 8 horas.
  - Links públicos protegidos por token UUID v4 y hash de contraseña opcional.
- **Vulnerabilidades y Riesgos:**
  - `SECRET_KEY` cae por defecto en valor hardcodeado si `.env` no existe.
  - Credenciales admin únicas configuradas en `.env` (no soporta múltiples usuarios ni roles granularizados).
  - Ausencia de Rate Limiting en `/api/auth/login` y `/api/public/{token}` (vulnerable a ataques de fuerza bruta).
  - CORS configurado con `allow_origins=["*"]` sin restricción en producción.
  - Ausencia de sanitización estricta de nombres de archivo y validación de tipos MIME al subir archivos.

---

## 7. Capacidad Actual de Importación y Arquitectura Objetivo

Actualmente la capacidad de importar archivos es **0% (Inexistente)**.

### Arquitectura Objetivo del Modelo de Datos (Fase 01-04):

```
+----------------+       +------------------+       +------------------+
|     CLIENT     | 1---* |   SOURCE_CONFIG  | 1---* |  KPI_CONFIG      |
+----------------+       +------------------+       +------------------+
        |                         |                          |
        | 1                       | 1                        | 1
        *                         *                          *
+----------------+       +------------------+       +------------------+
| MONTHLY_REPORT | 1---* |  REPORT_IMPORT   | 1---* |     METRIC       |
+----------------+       +------------------+       +------------------+
                                  |                          |
                                  | 1                        | 1
                                  *                          *
                         +------------------+       +------------------+
                         |     RAW_FILE     |       |       KPI        |
                         +------------------+       +------------------+
```
