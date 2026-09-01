# 🗄️ 03 — Modelo de Datos (FASE 01)

## Esquema Relacional Base

### 1. `clients`
- `id` (INTEGER, PK)
- `name` (STRING)
- `description` (TEXT)
- `color` (STRING)
- `logo_text` (STRING)
- `is_active` (BOOLEAN)
- `kpi_modules` (JSON) — Lista de identificadores de módulos activos.
- `created_at` (DATETIME)

### 2. `sources`
- `id` (INTEGER, PK)
- `name` (STRING) — Ej: "Yeastar Call Center", "Botmaker Chatbot", "Ingreso Manual".
- `code` (STRING, UNIQUE) — Ej: `yeastar`, `botmaker`, `manual`.
- `description` (TEXT)
- `is_active` (BOOLEAN)
- `created_at` (DATETIME)

### 3. `kpi_configs`
- `id` (INTEGER, PK)
- `client_id` (INTEGER, FK -> clients.id)
- `kpi_code` (STRING)
- `kpi_name` (STRING)
- `source_code` (STRING)
- `target_value` (FLOAT)
- `is_active` (BOOLEAN)
- `created_at` (DATETIME)

### 4. `audit_logs`
- `id` (INTEGER, PK)
- `username` (STRING)
- `action` (STRING) — Ej: `LOGIN_SUCCESS`, `CREATE_CLIENT`, `UPDATE_REPORT`, `VIEW_DASHBOARD_GLOBAL`.
- `resource_type` (STRING)
- `resource_id` (STRING)
- `details` (JSON)
- `ip_address` (STRING)
- `timestamp` (DATETIME)

### 5. `monthly_reports`
- `id` (INTEGER, PK)
- `client_id` (INTEGER, FK -> clients.id)
- `year` (INTEGER)
- `month` (INTEGER)
- `chats`, `leads`, `sales`, `appointment_confirmations`, `support`, `csat`
- `total_calls`, `answered_calls`, `contact_rate`, `inbound_calls`, `outbound_calls`
- `kidoz_*` (Evaluaciones de calidad Kidoz)
- `extra_data` (JSON) — Datos dinámicos por fuente (Yeastar/Botmaker).
- `notes` (TEXT)
- `created_at`, `updated_at` (DATETIME)

### 6. `public_views`
- `id` (INTEGER, PK)
- `client_id` (INTEGER, FK -> clients.id)
- `token` (STRING, UNIQUE)
- `title`, `description`, `visible_sections` (JSON)
- `password_hash`, `is_active`, `expires_at`, `views_count`
- `created_at` (DATETIME)
