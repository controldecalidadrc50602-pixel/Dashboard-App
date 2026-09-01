# 📊 Dashboard Reportes

Aplicación web para gestión de informes de clientes con panel admin, vista presentación y links públicos.

## 🚀 Instalación y arranque

### 1. Instalar dependencias
```powershell
cd C:\Users\Marilyn\.gemini\antigravity\scratch\dashboard-reportes
C:\Users\Marilyn\AppData\Local\Programs\Python\Python313\python.exe -m pip install -r requirements.txt
```

### 2. Cargar datos históricos (solo la primera vez)
```powershell
C:\Users\Marilyn\AppData\Local\Programs\Python\Python313\python.exe seed_data.py
```
Esto carga automáticamente todos los datos del reporte Rc506 (Enero–Agosto 2026).

### 3. Iniciar el servidor
```powershell
C:\Users\Marilyn\AppData\Local\Programs\Python\Python313\python.exe run.py
```

### 4. Abrir la aplicación
- **Panel admin:** http://localhost:8000
- **Usuario:** `admin` | **Contraseña:** `admin123`

---

## 🗂 Estructura de la app

| URL | Descripción |
|-----|------------|
| `http://localhost:8000/` | Login |
| `http://localhost:8000/admin` | Panel admin (Dashboard Global, Ingesta, Clientes, Reportes, Links) |
| `http://localhost:8000/slides/{id}` | Vista presentación (interna) |
| `http://localhost:8000/view/{token}` | Vista pública para el cliente |
| `http://localhost:8000/api/docs` | Documentación API (Swagger) |
| `http://localhost:8000/api/admin/imports/` | API de Ingesta & Conservación RAW |
| `http://localhost:8000/api/admin/imports/{id}/process` | API de Normalización & Reprocesamiento RAW |
| `http://localhost:8000/api/admin/imports/{id}/normalized-summary` | API de Métricas Operativas Base |
| `http://localhost:8000/api/admin/imports/{id}/quality` | API de Calidad & Trazabilidad por Fila |
| `http://localhost:8000/api/admin/kpis/clients/{client_id}` | API de Configuración de KPIs Dinámicos por Cliente |
| `http://localhost:8000/api/admin/kpis/calculate` | API de Evaluación & Cálculo Determinista de KPIs |
| `http://localhost:8000/api/admin/kpis/results` | API de Histórico de Resultados de KPIs |
| `http://localhost:8000/api/admin/kpis/results/{id}/traceability` | API de Trazabilidad Completa de KPI |
| `http://localhost:8000/api/admin/analysis/run` | API de Ejecución de Análisis Determinístico RC506 |
| `http://localhost:8000/api/admin/analysis/clients/{id}/insights` | API de Consulta de Insights & Alertas por Cliente |
| `http://localhost:8000/api/admin/analysis/insights/{id}/traceability` | API de Trazabilidad Fila RAW ➔ Insight RC506 |






---

## 📱 Cómo usar

### Agregar un nuevo mes
1. Ve a **Reportes mensuales** en el sidebar
2. Selecciona el cliente en la parte superior
3. Haz clic en **Agregar mes**
4. Llena el formulario y guarda

### Generar link para el cliente
1. Ve a **Links públicos** en el sidebar
2. Haz clic en **Crear link**
3. Pon un título, elige qué secciones mostrar
4. Opcionalmente agrega contraseña o fecha de expiración
5. Copia el link y compártelo con tu cliente

### Ver presentación
- Desde el panel de Clientes, haz clic en el ícono de presentación
- Navega con las flechas ← → del teclado o con los botones
- Presiona `F` para pantalla completa

---

## 🔒 Seguridad

- Cambia la contraseña en el archivo `.env` antes de usar en producción
- El archivo `.env` nunca debe subirse a git (está en .gitignore)
- Los links públicos no exponen datos del panel admin
- Puedes poner contraseña y/o fecha de expiración a cada link

---

## 🌐 Para acceso público (Internet)

Si quieres que el link del cliente funcione desde internet (sin estar en tu red local):

### Opción A: Railway (gratis)
1. Crea cuenta en https://railway.app
2. Conecta el repositorio
3. Railway despliega automáticamente

### Opción B: Ngrok (temporal, para demos)
```powershell
ngrok http 8000
```
Genera un link temporal tipo `https://abc123.ngrok.io`

---

## ⚙️ Variables de entorno (.env)

```
ADMIN_USERNAME=admin          # Usuario del panel
ADMIN_PASSWORD=admin123       # CAMBIA ESTO
SECRET_KEY=tu-clave-secreta   # CAMBIA ESTO
DATABASE_URL=sqlite:///./dashboard.db
```
