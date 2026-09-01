# 💻 04. Interfaces y Vistas del Sistema

## 🖥️ 1. Panel Administrativo (`/admin`)

- **Navegación Sidebar:**
  - **Dashboard:** Tarjetas dinámicas de KPIs y cuadrícula de gráficos adaptativos según el cliente seleccionado.
  - **Clientes:** Gestión de clientes, avatares, colores y asignación de **Módulos KPI Habilitados**.
  - **Reportes Mensuales:** Tabla de datos históricos con columnas dinámicas adaptadas al cliente activo (Kidoz vs Petopia).
  - **Links Públicos:** Generación de enlaces con selección de secciones visibles, contraseña y vencimiento.
- **Selector Global de Cliente:**
  - Ubicado en la barra superior; permite alternar instantáneamente todo el contexto del admin entre Kidoz, Petopia o cualquier nuevo cliente.

---

## 📽️ 2. Modo Presentación Diapositivas (`/slides/{id}`)

- **Uso:** Diseñado para reuniones ejecutivas con clientes.
- **Características:**
  - Diapositiva 0: Portada elegante con periodo y métricas globales.
  - Diapositiva 1: KPIs Ejecutivos & Gráficos principales.
  - Diapositiva 2: Tabla Consolidada mensual con indicadores de tendencia (▲/▼).
  - Diapositiva 3: Tendencias & Análisis comparativo.
  - Diapositiva 4: Cierre con marca de agua y fecha.
  - Controles: Flechas de teclado `←` `→`, botones navegadores y modo **Pantalla Completa** (`F`).

---

## 🌐 3. Vista Pública para Clientes (`/view/{token}`)

- **Uso:** El enlace que se entrega al cliente final para consultar su reporte.
- **Características:**
  - **Puerta de Contraseña (Password Gate):** Si el admin protegió el enlace, solicita contraseña antes de cargar datos.
  - **Sin Acceso al Admin:** No expone credenciales ni datos de otros clientes.
  - **Renderizado Dinámico:**
    - Para **Kidoz**: Muestra métricas comerciales, embudo de conversión y calidad KIDOZ.
    - Para **Petopia**: Muestra volúmenes de atención Yeastar (Agentes) + Botmaker (Bot) y tablas consolidadas.
