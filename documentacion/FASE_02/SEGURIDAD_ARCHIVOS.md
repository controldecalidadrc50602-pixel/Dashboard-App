# 🔒 FASE 02 — Seguridad & Almacenamiento RAW

## Controles de Seguridad Aplicados

### 1. Inmutabilidad y Aislamiento de Archivos
- Los archivos subidos se almacenan en `uploads/raw/` utilizando identificadores únicos UUID (`<uuid>.<ext>`).
- Se ignora completamente el nombre de archivo original en el sistema de archivos del servidor para prevenir ataques de **Path Traversal** (`../../etc/passwd`).

### 2. Bloqueo de Extensiones Ejecutables
- Se rechazan de forma estricta extensiones peligrosas: `.exe`, `.dll`, `.so`, `.bat`, `.cmd`, `.sh`, `.py`, `.js`, `.vbs`, `.php`, `.asp`, `.ps1`.

### 3. Límite de Tamaño
- Límite máximo por archivo configurado en **50 MB** (`MAX_FILE_SIZE_BYTES`).

### 4. Trazabilidad Criptográfica (SHA-256)
- Identificación idempotente única de 64 caracteres Hex por contenido de archivo.

### 5. Auditoría de Accesos
- Peticiones a `GET /api/admin/imports/{id}/preview` o descarga RAW registran el evento `RAW_FILE_ACCESSED` en `audit_logs`.
