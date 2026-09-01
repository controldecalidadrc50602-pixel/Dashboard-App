# 🧪 FASE 02 — Informe de Pruebas Automatizadas

**SUITE DE PRUEBAS:** `tests/test_fase02.py`  
**RESULTADO:** **15/15 PASSED (100%)**

## Detalle de Casos de Prueba
1. `test_01_import_botmaker_users`: Ingesta correcta de `users-2026.09.01-20.31.tsv`. (PASSED)
2. `test_02_import_operators_sessions_debug`: Ingesta correcta de `operatorsSessionsDebug-2026.09.01-20.31.tsv`. (PASSED)
3. `test_03_import_session_starting_causes`: Ingesta correcta de `sessionStartingCauses-2026.09.01-20.31.tsv`. (PASSED)
4. `test_04_detect_tsv_correctly`: Detección precisa del delimitador `\t` y formato `tsv`. (PASSED)
5. `test_05_validate_headers`: Detección de columnas clave omitidas con generación de warnings. (PASSED)
6. `test_06_generate_sha256`: Generación de hash SHA-256 de 64 caracteres. (PASSED)
7. `test_07_detect_duplicate_file`: Detección idempotente de duplicados resultando en estado `DUPLICATE`. (PASSED)
8. `test_08_reject_disallowed_extension`: Bloqueo de extensiones peligrosas (.exe/.py) retornando HTTP 400. (PASSED)
9. `test_09_reject_oversized_file`: Bloqueo de archivos superiores a 50 MB retornando HTTP 400. (PASSED)
10. `test_10_record_row_errors_without_silent_loss`: Registro de advertencias en filas malformadas sin omisión silenciosa. (PASSED)
11. `test_11_save_import_metadata`: Registro de encoding, delimitador, headers y total de registros en metadata JSON. (PASSED)
12. `test_12_preserve_raw_file`: Conservación inmutable del contenido RAW en disco en la ruta `storage_path`. (PASSED)
13. `test_13_verify_authorization`: Bloqueo HTTP 401 en accesos no autenticados a `/api/admin/imports/`. (PASSED)
14. `test_14_verify_audit_logging`: Emisión de eventos `IMPORT_STARTED`, `IMPORT_COMPLETED` y `RAW_FILE_ACCESSED` en `audit_logs`. (PASSED)
15. `test_15_verify_fase01_compatibility`: Verificación de compatibilidad total con endpoints de Fase 01 (Dashboard Global, Clientes, Links públicos, Slides). (PASSED)
