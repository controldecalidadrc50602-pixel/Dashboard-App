# 🔌 03. API, Modelos de Datos y Módulos KPI

## 🗄️ Modelos de Base de Datos (SQLAlchemy)

### 1. `Client` (Tabla `clients`)
- `id` (Integer, Primary Key)
- `name` (String) - Nombre del cliente (ej: Kidoz, Petopia)
- `description` (Text)
- `color` (String) - Color hexadecimal distintivo
- `logo_text` (String) - Texto iniciales del avatar (ej: KZ, PT)
- `kpi_modules` (JSON) - Array de módulos activados (ej: `["chat_sales", "quality_kidoz"]`)
- `is_active` (Boolean)
- `created_at` (DateTime)

### 2. `MonthlyReport` (Tabla `monthly_reports`)
- `id` (Integer, Primary Key)
- `client_id` (ForeignKey `clients.id`)
- `year` (Integer) & `month` (Integer)
- `chats`, `leads`, `sales`, `appointment_confirmations`, `support`, `csat`
- `total_calls`, `answered_calls`, `contact_rate`, `inbound_calls`, `outbound_calls`
- `kidoz_optimal_calls`, `kidoz_optimal_chats`, `kidoz_optimal_pct`
- `extra_data` (JSON) - Objeto flexible para datos de volumen Yeastar/Botmaker o métricas personalizadas.
- `notes` (Text) - Observaciones del mes.

### 3. `PublicView` (Tabla `public_views`)
- `id` (Integer, Primary Key)
- `client_id` (ForeignKey `clients.id`)
- `token` (String, Unique Index) - UUID del enlace público
- `title` (String) & `description` (Text)
- `visible_sections` (JSON) - Array de secciones habilitadas para el cliente
- `password_hash` (String, Opcional)
- `expires_at` (DateTime, Opcional)
- `views_count` (Integer)

---

## 📡 Endpoints de la API REST

### Autenticación
- `POST /api/auth/login` → Autentica al admin y retorna el Token JWT.

### Clientes (Protegido por Bearer Token)
- `GET /api/clients/` → Lista todos los clientes y sus `kpi_modules`.
- `POST /api/clients/` → Crea un nuevo cliente con sus módulos de KPI.
- `PUT /api/clients/{id}` → Actualiza cliente y sus módulos habilitados.
- `DELETE /api/clients/{id}` → Elimina cliente y sus datos asociados.

### Reportes Mensuales (Protegido por Bearer Token)
- `GET /api/clients/{id}/reports` → Lista reportes filtrables por año.
- `POST /api/clients/{id}/reports` → Agrega un nuevo mes de datos.
- `PUT /api/clients/{id}/reports/{report_id}` → Edita un reporte existente.
- `DELETE /api/clients/{id}/reports/{report_id}` → Elimina un reporte.

### Links Públicos (Acceso Cliente)
- `GET /api/clients/{id}/public-views` → (Admin) Lista links del cliente.
- `POST /api/clients/{id}/public-views` → (Admin) Crea un nuevo link público.
- `GET /api/public/{token}` → (Público) Retorna los datos filtrados del cliente según las secciones habilitadas.
