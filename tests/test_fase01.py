import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database import Base, get_db
from app.main import app
from app.models import Client, MonthlyReport, PublicView, Source, KPIConfig, ReportImport
from app.auth import create_access_token, hash_password


# Crear BD SQLite en memoria para la suite de pruebas
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    """Limpia y re-crea el esquema antes de cada prueba y aísla la base de datos."""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def get_admin_headers():
    token = create_access_token({"sub": "admin", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


# ── PRUEBA 1: Dashboard global sin clientes ──────────────────────────────
def test_dashboard_global_sin_clientes():
    response = client.get("/api/admin/dashboard-global", headers=get_admin_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_active_clients"] == 0
    assert data["summary"]["clients_with_data"] == 0
    assert len(data["client_statuses"]) == 0
    assert data["global_metrics"]["total_chats"] == 0


# ── PRUEBA 2: Dashboard global con Kidoz ────────────────────────────────
def test_dashboard_global_con_kidoz():
    db = TestingSessionLocal()
    c_kidoz = Client(name="Kidoz", description="Clínica Kidoz", color="#009688", logo_text="KD", is_active=True)
    db.add(c_kidoz)
    db.commit()
    db.refresh(c_kidoz)

    rep = MonthlyReport(client_id=c_kidoz.id, year=2026, month=8, chats=150, leads=30, sales=10, csat=4.8)
    db.add(rep)
    db.commit()
    db.close()

    response = client.get("/api/admin/dashboard-global", headers=get_admin_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_active_clients"] == 1
    assert data["summary"]["clients_with_data"] == 1
    assert data["client_statuses"][0]["name"] == "Kidoz"
    assert data["client_statuses"][0]["status"] == "actualizado"
    assert data["global_metrics"]["total_chats"] == 150


# ── PRUEBA 3: Dashboard global con Petopia ──────────────────────────────
def test_dashboard_global_con_petopia():
    db = TestingSessionLocal()
    c_petopia = Client(name="Petopia", description="Petopia Vet", color="#ff9800", logo_text="PT", is_active=True, kpi_modules=["petopia_vol"])
    db.add(c_petopia)
    db.commit()
    db.refresh(c_petopia)

    rep = MonthlyReport(
        client_id=c_petopia.id, year=2026, month=8,
        total_calls=450,
        extra_data={"yeastar_calls": 450, "botmaker_interactions": 300}
    )
    db.add(rep)
    db.commit()
    db.close()

    response = client.get("/api/admin/dashboard-global", headers=get_admin_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_active_clients"] == 1
    assert data["client_statuses"][0]["name"] == "Petopia"
    assert data["global_metrics"]["total_calls"] == 450


# ── PRUEBA 4: Dashboard global con múltiples clientes ──────────────────
def test_dashboard_global_multiples_clientes():
    db = TestingSessionLocal()
    c1 = Client(name="Cliente A", color="#111111", is_active=True)
    c2 = Client(name="Cliente B", color="#222222", is_active=True)
    db.add_all([c1, c2])
    db.commit()

    db.add(MonthlyReport(client_id=c1.id, year=2026, month=8, chats=100))
    db.add(MonthlyReport(client_id=c2.id, year=2026, month=8, chats=200))
    db.commit()
    db.close()

    response = client.get("/api/admin/dashboard-global", headers=get_admin_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_active_clients"] == 2
    assert data["summary"]["clients_with_data"] == 2
    assert data["global_metrics"]["total_chats"] == 300


# ── PRUEBA 5: Cliente inactivo ─────────────────────────────────────────
def test_cliente_inactivo():
    db = TestingSessionLocal()
    c_inactivo = Client(name="Cliente Inactivo", is_active=False)
    db.add(c_inactivo)
    db.commit()
    db.close()

    response = client.get("/api/admin/dashboard-global", headers=get_admin_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_active_clients"] == 0
    assert data["client_statuses"][0]["status"] == "inactivo"
    assert data["client_statuses"][0]["status_label"] == "Inactivo"


# ── PRUEBA 6: Cliente sin reportes ─────────────────────────────────────
def test_cliente_sin_reportes():
    db = TestingSessionLocal()
    c_nuevo = Client(name="Nuevo Cliente", is_active=True, kpi_modules=["chat_sales"])
    db.add(c_nuevo)
    db.commit()
    db.close()

    response = client.get("/api/admin/dashboard-global", headers=get_admin_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_active_clients"] == 1
    assert data["summary"]["clients_with_data"] == 0
    assert data["client_statuses"][0]["status"] in ["pendiente", "requiere_configuracion"]


# ── PRUEBA 7: Cliente con reportes históricos ─────────────────────────
def test_cliente_reportes_historicos():
    db = TestingSessionLocal()
    c_hist = Client(name="Cliente Historico", is_active=True)
    db.add(c_hist)
    db.commit()

    db.add(MonthlyReport(client_id=c_hist.id, year=2025, month=12, chats=80))
    db.add(MonthlyReport(client_id=c_hist.id, year=2026, month=1, chats=90))
    db.commit()
    db.close()

    response = client.get("/api/admin/dashboard-global", headers=get_admin_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["clients_with_data"] == 1
    assert data["client_statuses"][0]["total_reports"] == 2


# ── PRUEBA 8: Usuario no autenticado (401) ────────────────────────────
def test_usuario_no_autenticado():
    response = client.get("/api/admin/dashboard-global")
    assert response.status_code == 401


# ── PRUEBA 9: Acceso no autorizado (token inválido) ───────────────────
def test_acceso_no_autorizado_token_invalido():
    response = client.get("/api/admin/dashboard-global", headers={"Authorization": "Bearer token-invalido-123"})
    assert response.status_code == 401


# ── PRUEBA 10: Cliente inexistente (404) ──────────────────────────────
def test_cliente_inexistente_404():
    response = client.get("/api/clients/99999", headers=get_admin_headers())
    assert response.status_code == 404
    assert response.json()["detail"] == "Cliente no encontrado"


# ── PRUEBA 11: Compatibilidad del dashboard individual ───────────────
def test_compatibilidad_dashboard_individual():
    db = TestingSessionLocal()
    c = Client(name="Cliente Test", is_active=True)
    db.add(c)
    db.commit()
    c_id = c.id

    db.add(MonthlyReport(client_id=c_id, year=2026, month=5, chats=120, sales=15, leads=30))
    db.commit()
    db.close()

    response = client.get(f"/api/clients/{c_id}/reports", headers=get_admin_headers())
    assert response.status_code == 200
    reports = response.json()
    assert len(reports) == 1
    assert reports[0]["closing_rate"] == 50.0
    assert reports[0]["month_name"] == "Mayo"


# ── PRUEBA 12: Compatibilidad de slides ────────────────────────────────
def test_compatibilidad_slides():
    db = TestingSessionLocal()
    c = Client(name="Cliente Slides", is_active=True)
    db.add(c)
    db.commit()
    c_id = c.id
    db.close()

    response = client.get(f"/slides/{c_id}")
    assert response.status_code == 200
    assert "<html" in response.text.lower() or "<!doctype html>" in response.text.lower()



# ── PRUEBA 13: Compatibilidad de links públicos ───────────────────────
def test_compatibilidad_links_publicos():
    db = TestingSessionLocal()
    c = Client(name="Cliente Publico", is_active=True)
    db.add(c)
    db.commit()

    pv = PublicView(
        client_id=c.id, token="token-test-123",
        title="Informe Público", visible_sections=["general", "chats"]
    )
    db.add(pv)
    db.commit()
    db.close()

    response = client.get("/api/public/token-test-123")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Informe Público"
    assert data["client"]["name"] == "Cliente Publico"
