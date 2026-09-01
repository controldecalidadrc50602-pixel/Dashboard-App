# ⚠️ FASE 05B — Limitaciones Conocidas de Persistencia en Vercel Serverless

## Diagnóstico Técnico sobre SQLite en Vercel
1. **Sistema de Archivos Efímero:** Vercel ejecuta código Python en instancias AWS Lambda aisladas y efímeras. El directorio `/tmp` es de solo escritura temporal por invocación y se destruye cuando la instancia Lambda se apaga o reinicia.
2. **Impacto en Datos:**
   - La base de datos SQLite `/tmp/dashboard.db` se reinicializa al crearse una nueva instancia Serverless.
   - Los datos creados en una sesión (clientes creados dinámicamente, archivos subidos a `/tmp/uploads/raw`) son **efímeros**.

## Estado Clasificado
- **DEPLOYMENT:** FUNCIONAL (La aplicación compila, ejecuta, sirve plantillas y responde APIs).
- **PERSISTENCIA DE PRODUCCIÓN:** PENDIENTE (Requiere base de datos administrada como PostgreSQL / Neon / Supabase para producción persistente a largo plazo).
