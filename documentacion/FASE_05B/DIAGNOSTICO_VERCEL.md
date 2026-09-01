# 🩺 FASE 05B — Diagnóstico de Causas de Fallo en Vercel

## Causas Encontradas del Error 500 / FUNCTION_INVOCATION_FAILED

### 1. Ausencia de `includeFiles` en `vercel.json` (Empaquetado Serverless)
- **Problema:** Vercel empaqueta únicamente archivos Python por defecto. Las plantillas HTML (`templates/login.html`, `templates/admin.html`) y assets estáticos no se incluyeron en la compilación de la función Serverless `api/index.py`.
- **Efecto:** Al acceder a `/`, Jinja2 intentaba buscar `templates/login.html` y lanzaba `TemplateNotFound: login.html`, ocasionando el colapso 500 de la función.

### 2. Firma Incompatible de `TemplateResponse` con Starlette 0.36+ / FastAPI 0.111+
- **Problema:** `TemplateResponse("login.html", {"request": request})` es deprecado e incompatible con versiones recientes de Starlette que esperan `TemplateResponse(request, name)` o `TemplateResponse(request=request, name=name)`.
- **Efecto:** Al invocar la plantilla, se lanzaba una excepción `AttributeError` interna.

### 3. Resolución de Módulos (`sys.path`)
- **Problema:** En el entorno Serverless, la ejecución desde `/var/task/api/index.py` no siempre resolvía el módulo de nivel superior `app`.
- **Efecto:** `ModuleNotFoundError: No module named 'app'`.

---

## Matriz de Clasificación del Fallo
- **Build Vercel:** OK (La función se compilaba).
- **Runtime Serverless:** FALLIDO (Faltaban archivos de plantillas HTML y firma de `TemplateResponse`).
- **Routing:** OK (Vercel redirige a `api/index.py`).
- **Database SQLite:** FUNCIONAL sobre `/tmp/dashboard.db` (Limitación efímera documentada).
