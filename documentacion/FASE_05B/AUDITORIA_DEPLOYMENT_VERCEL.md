# 📑 FASE 05B — AUDITORÍA TÉCNICA DEL DESPLIEGUE EN VERCEL

**AGENTE / AUDITOR:** Kairos — Arquitecto Principal, Auditor Técnico y Desarrollador Senior  
**PROYECTO:** RC506 Reporting  
**FASE:** FASE 05B --- Auditoría y Corrección del Despliegue Vercel  
**FECHA:** 2026-09-01  

---

## 1. Contexto y Motivo del Bloqueo
Tras la entrega de la Fase 05, la aplicación no cargaba su contenido HTML/JS en la URL pública de Vercel (`dashboard-app-one-mu-79.vercel.app`), arrojando errores `500: INTERNAL_SERVER_ERROR (FUNCTION_INVOCATION_FAILED)`.

Se detuvo cualquier avance hacia la Fase 06 bajo la **REGLA DE BLOQUEO TÉCNICO** hasta diagnosticar, corregir y verificar el despliegue Serverless en Vercel.

---

## 2. Inspección del Repositorio y Arquitectura Serverless
Se auditó la configuración de empaquetado de Vercel:
- **`vercel.json`:** Contenía únicamente la regla de reescritura de rutas (`rewrites` a `/api/index`), sin especificar los archivos no de Python a empaquetar en el paquete Lambda.
- **`templates/` y `static/`:** Directorios fuera del paquete predeterminado de Python en Vercel.
- **Firma de `TemplateResponse`:** Firma heredada en `app/main.py` pasando `TemplateResponse("login.html", {"request": request})`, lo cual genera `AttributeError` en Starlette 0.36+/FastAPI 0.111+.
- **Base de Datos SQLite Serverless:** Comprobación del uso de `/tmp/dashboard.db` en el sistema de archivos efímero de AWS Lambda / Vercel.
