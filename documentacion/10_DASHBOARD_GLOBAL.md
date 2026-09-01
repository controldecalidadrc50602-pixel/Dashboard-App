# 📊 10 — Dashboard Global RC506 (FASE 01)

## Descripción
El Dashboard Global RC506 es el centro de control ejecutivo de la agencia RC506. Permite supervisar en tiempo real la salud del reporting de todos los clientes activos sin ingresar individualmente a cada cuenta.

## Endpoint API
`GET /api/admin/dashboard-global`

### Protección & Autorización
- Header: `Authorization: Bearer <token_jwt_admin>`
- Código HTTP 401 si no está autenticado o el rol no es `admin`.

### Lógica de Negocio y Reglas Explícitas

#### 1. Período Global (`latest_period`)
Se calcula dinámicamente identificando el período `(año, mes)` más reciente disponible entre todos los reportes de la base de datos.

#### 2. Regla de Estado de Reporting por Cliente (`status`)
Para cada cliente en la base de datos:
- `inactivo`: Si `is_active == False`.
- `actualizado`: Si posee un reporte cargado en el período global más reciente.
- `pendiente`: Si tiene reportes en la base de datos pero le falta el del período global más reciente.
- `requiere_configuracion`: Si el cliente está activo pero no posee KPIs ni reportes configurados.

#### 3. Métricas Consolidadas Comparables (`global_metrics`)
Solo se agregan métricas cuantitativas homogéneas a nivel agencia:
- `total_chats`: Suma total de chats gestionados.
- `total_calls`: Suma total de llamadas en sistema.
- `total_leads`: Suma total de leads calificados.
- `total_sales`: Suma total de ventas registradas.
- `avg_csat`: Promedio aritmético de satisfacción (CSAT) entre clientes con mediciones.

#### 4. Alertas Preliminares RC506 (`preliminary_alerts`)
Identifican proactivamente:
- Clientes con reportes pendientes para el período actual.
- Clientes que requieren configuración inicial de KPIs.

#### 5. Auditoría de Operaciones (`recent_activity`)
Muestra las últimas 10 operaciones administrativas registradas en `audit_logs`.
