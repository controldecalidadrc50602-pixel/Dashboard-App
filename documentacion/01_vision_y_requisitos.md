# 📄 01. Visión del Proyecto y Requisitos

## 📌 Visión General
**Dashboard Reportes** es una plataforma web integral diseñada para la gestión, seguimiento y presentación de informes mensuales de clientes. 

Permite a la agencia/empresa administradora (**Rc506**):
1. **Llevar un histórico de datos mensuales** por cada cliente.
2. **Personalizar los KPIs y métricas** que cada cliente mide (ej: ventas vs. volumen telefónico/bot).
3. **Presentar informes ejecutivos en formato diapositivas (Slides)** listos para reuniones.
4. **Generar enlaces públicos seguros y limpios** para que el cliente consulte sus reportes sin acceder al panel administrativo.

---

## 🎯 Objetivos Principales

- **Multi-Cliente & Multi-KPI:** Cada cliente puede tener módulos de métricas totalmente independientes.
- **Acceso Cliente Seguro (Public Links):** Enlaces únicos por token con secciones seleccionables y opción de clave/expiración.
- **Formato Presentación Incorporado:** Vista tipo slides con navegación por teclado y modo pantalla completa.
- **Histórico & Escalabilidad:** Almacenamiento centralizado de datos por año y mes.

---

## 👥 Clientes de Ejemplo e Identidad

### 1. Rc506 (Empresa Administradora)
- Es la marca/agencia que administra la plataforma y gestiona los informes de los clientes.

### 2. Kidoz (Cliente 1 - Centro de Neurodesarrollo)
- **Enfoque de KPIs:** Gestión comercial y calidad de atención.
- **Módulos activos:**
  - 💬 Chats gestionados, Leads generados, Ventas cerradas, % Efectividad de Cierre.
  - 📅 Confirmaciones de citas y Tickets de soporte.
  - ⭐ Calidad de Atención KIDOZ (% Óptimo) y CSAT (0-5).
  - 📞 Llamadas totales y tasa de contacto.

### 3. Petopia (Cliente 2 - Servicios Veterinarios)
- **Enfoque de KPIs:** Volumen de atención telefónica y automatización.
- **Módulos activos:**
  - 📞 **Yeastar:** Volumen de llamadas atendidas por agentes humanos.
  - 🤖 **Botmaker:** Volumen de interacciones procesadas por el bot.
  - 📊 **Consolidado:** Tendencias combinadas y mapas de actividad.

---

## ⚙️ Módulos KPI Disponibles

| Código Módulo | Nombre | Descripción |
|---------------|--------|-------------|
| `chat_sales` | 💬 Chats, Leads & Ventas | Métricas de conversión y embudo comercial |
| `appointments` | 📅 Confirmaciones Cita | Citas confirmadas y soporte |
| `calls` | 📞 Llamadas Detalladas | Entrantes, salientes y tasa de contacto |
| `quality_kidoz` | ⭐ Calidad de Atención | Evaluaciones óptimas/aceptables/deficientes y CSAT |
| `petopia_vol` | 🐾 Volumen Yeastar & Botmaker | Métricas de volumen combinado agente + bot |
