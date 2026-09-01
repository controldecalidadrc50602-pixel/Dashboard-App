# 🔒 14 — Seguridad & Auditoría (FASE 01)

## Calificación de Seguridad: 7.0 / 10 (Línea Base: 4.5 / 10)

## Mejoras Implementadas en Fase 01

### 1. Auditoría Persistente (`AuditLog`)
Toda acción administrativa de modificación o acceso sensible es registrada en la tabla `audit_logs`:
- Intentos de inicio de sesión (`LOGIN_SUCCESS`, `LOGIN_FAILED`).
- Gestión de Clientes (`CREATE_CLIENT`, `UPDATE_CLIENT`, `DELETE_CLIENT`).
- Gestión de Reportes (`CREATE_REPORT`, `UPDATE_REPORT`, `DELETE_REPORT`).
- Visualización de la vista global (`VIEW_DASHBOARD_GLOBAL`).

### 2. Autenticación y Autorización JWT
- Token JWT con algoritmo `HS256`, emisión de `iat` (issued at) y expiración `exp` (480 min).
- Verificación de claim `role == 'admin'` en la dependencia `get_current_admin`.

### 3. Verificación de SECRET_KEY
- Detección proactiva con advertencias de log si la clave se mantiene en el valor por defecto de desarrollo (`dev-secret-key-change-in-production`).

### 4. Sanitización de Errores
- Respuestas HTTP estandarizadas (`401 Unauthorized`, `404 Not Found`, `409 Conflict`) sin volcado de trazas ni excepciones del ORM hacia los usuarios.

## Riesgos Residuales & Pendientes para Fases Posteriores
- Incorporar Rate Limiting a nivel IP en endpoints de autenticación (`/api/auth/login`).
- Soporte para expiración configurable en enlaces públicos protegidos por contraseña.
