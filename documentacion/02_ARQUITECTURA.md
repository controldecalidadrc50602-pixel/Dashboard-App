# 🏛️ 02 — Arquitectura del Sistema (FASE 01)

## Visión General
RC506 Reporting es una plataforma desacoplada multi-cliente diseñada para escalar a más de 30+ clientes independientes y múltiples fuentes de datos (Yeastar Call Center, Botmaker Chatbot, Ingresos Manuales y APIs futuras).

```
                 ┌──────────────────────────────────────┐
                 │        PANEL ADMIN RC506 UI         │
                 │   (templates/admin.html + JS SPA)   │
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────────┐
                 │           FASTAPI ROUTERS            │
                 ├──────────────────┬───────────────────┤
                 │ /api/admin/dash..│ /api/clients/*    │
                 │ /api/auth/*      │ /api/public/*     │
                 └──────────────────┼───────────────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────────┐
                 │       SERVICIOS Y MODELOS ORM        │
                 │  Client | Source | KPIConfig | Audit │
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────────┐
                 │        SQLITE / DATABASE ENGINE      │
                 │             dashboard.db             │
                 └──────────────────────────────────────┘
```

## Principios Arquitectónicos
1. **Desacoplamiento Nivel Agencia (RC506) vs Nivel Cliente:**
   - **Dashboard Global RC506:** Vista ejecutiva consolidada independiente de la configuración específica de un cliente.
   - **Dashboard Individual:** Vista adaptativa según los módulos KPI activos (`kpi_modules` / `kpi_configs`).
2. **Soporte Multi-Fuente:**
   - La entidad `Source` desacopla la procedencia de los datos (Yeastar, Botmaker, Manual).
3. **Seguridad y Auditoría:**
   - Control de acceso por token JWT Bearer.
   - Trazabilidad persistente de operaciones en `AuditLog`.
