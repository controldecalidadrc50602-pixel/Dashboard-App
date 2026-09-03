from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

load_dotenv()

from app.database import Base, engine, SessionLocal
import app.models
from app.routers import auth, clients, reports, public, dashboard_global, imports, kpis, analysis, users
from app.dependencies import seed_default_users

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Búsqueda limpia y directa de plantillas
templates_dir = os.path.join(BASE_DIR, "templates")
if not os.path.exists(templates_dir):
    templates_dir = "templates"

templates = Jinja2Templates(directory=templates_dir)

# Inicialización de base de datos
try:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_default_users(db)
    db.close()
except Exception as e:
    print(f"Advertencia al inicializar tablas de BD: {e}")


app = FastAPI(title="Dashboard Reportes", version="1.0.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Montar estáticos si existen
static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Registrar routers principales
app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(reports.router)
app.include_router(public.router)
app.include_router(dashboard_global.router)
app.include_router(imports.router)
app.include_router(kpis.router)
app.include_router(analysis.router)
app.include_router(users.router)








# Middleware de restauración de path original para Vercel Serverless
@app.middleware("http")
async def fix_vercel_path_middleware(request: Request, call_next):
    # Vercel provee la ruta original enviada por el cliente en 'x-matched-path' o 'x-forwarded-path'
    matched_path = request.headers.get("x-matched-path") or request.headers.get("x-forwarded-path")
    if matched_path and matched_path != request.scope.get("path"):
        # Limpiar cualquier query string si viniera en el header
        clean_path = matched_path.split("?")[0]
        request.scope["path"] = clean_path
    
    print(f"METHOD: {request.method} | FINAL_PATH: {request.scope.get('path')}")
    return await call_next(request)



# ── Rutas de páginas HTML ──────────────────────────────────────────────────
@app.get("/")
@app.get("/api/index")
@app.get("/api/index.py")
def home(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/admin")
def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html")

@app.get("/slides/{client_id}")
def slides_page(request: Request, client_id: int):
    return templates.TemplateResponse(request=request, name="slides.html", context={"client_id": client_id})

@app.get("/view/{token}")
def public_view_page(request: Request, token: str):
    return templates.TemplateResponse(request=request, name="public.html", context={"token": token})


