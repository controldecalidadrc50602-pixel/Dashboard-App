# 🏗️ 02. Arquitectura del Sistema y Estructura de Código

## 📐 Arquitectura General

La aplicación sigue una arquitectura **Full-Stack ligera y modular**:

```
[ Frontend: HTML5 / Glassmorphic CSS / Vanilla JS / Chart.js ]
                             │
                             ▼ (HTTP Fetch API + JWT Auth)
[ Backend: FastAPI (Python 3.13) + Pydantic V2 ]
                             │
                             ▼ (SQLAlchemy 2.0 ORM)
[ Base de Datos: SQLite (Desarrollo) / PostgreSQL (Producción) ]
```

---

## 📁 Estructura de Directorios

```
dashboard-reportes/
├── run.py                       # Punto de entrada para iniciar Uvicorn
├── requirements.txt             # Dependencias del proyecto Python
├── .env                         # Variables de entorno (Credenciales, JWT, DB)
├── dashboard.db                 # Base de datos SQLite local
├── seed_data.py                 # Carga inicial de datos Kidoz
├── seed_petopia.py              # Carga inicial de datos Petopia
├── migrate.py                   # Script de migración de esquema DB
│
├── app/                         # Paquete Backend Python
│   ├── __init__.py
│   ├── main.py                  # Aplicación FastAPI, CORS y rutas HTML
│   ├── database.py              # Configuración SQLAlchemy Engine y Sessions
│   ├── models.py                # Modelos ORM (Client, MonthlyReport, PublicView)
│   ├── schemas.py               # Validadores Pydantic V2
│   ├── auth.py                  # Autenticación JWT y hashing bcrypt
│   └── routers/
│       ├── auth.py              # POST /api/auth/login
│       ├── clients.py           # CRUD /api/clients/
│       ├── reports.py           # CRUD /api/clients/{id}/reports/
│       └── public.py            # Links públicos y endpoint token
│
├── templates/                   # Plantillas Jinja2 (HTML Frontend)
│   ├── login.html               # Pantalla de inicio de sesión
│   ├── admin.html               # Panel de administración SPA
│   ├── slides.html              # Vista de presentación en diapositivas
│   └── public.html              # Vista cliente limpia y adaptativa
│
├── static/                      # Recursos estáticos (CSS, JS, imágenes)
│
└── documentacion/               # Documentación completa del sistema (.md)
    ├── 01_vision_y_requisitos.md
    ├── 02_arquitectura_y_estructura.md
    ├── 03_api_y_modulos.md
    ├── 04_interfaces_y_vistas.md
    ├── 05_historial_cambios_y_planes.md
    └── 06_guia_despliegue_firebase_vercel.md
```

---

## 🛠️ Tecnologías Utilizadas

- **Backend:** Python 3.13, FastAPI 0.111.0, Uvicorn 0.29.0
- **ORM & DB:** SQLAlchemy 2.0.36, SQLite / PostgreSQL
- **Seguridad:** JWT (`python-jose`), Passlib `bcrypt`
- **Frontend:** Jinja2 Templates, HTML5, Modern Glassmorphism CSS, Vanilla JS, Chart.js 4.4.0, FontAwesome 6.0
