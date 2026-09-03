import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.auth import create_access_token
from app.dependencies import seed_default_users
from app.models import Client, PublicView

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
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_default_users(db)

    # Crear cliente de prueba
    test_client = Client(name="Cliente Cualitativo Test", color="#009688")
    db.add(test_client)
    db.commit()
    db.refresh(test_client)

    # Crear link público de prueba
    pub_view = PublicView(client_id=test_client.id, token="token-test-qualitative", title="Reporte Cualitativo", visible_sections=["general"])
    db.add(pub_view)
    db.commit()

    db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def get_headers(username: str, role: str):
    token = create_access_token({"sub": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_01_create_qualitative_analysis_superadmin():
    admin_headers = get_headers("admin", "superadmin")
    payload = {
        "critical_points": "Atención prioritaria en tiempo de espera",
        "warnings": "Ligero incremento en volumen de mensajes",
        "achievements": "Meta de CSAT cumplida en 4.9",
        "general_info": "Campañas activadas con éxito"
    }

    res = client.post("/api/admin/clients/1/qualitative/2026-09", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["client_id"] == 1
    assert data["period"] == "2026-09"
    assert data["critical_points"] == "Atención prioritaria en tiempo de espera"
    assert data["achievements"] == "Meta de CSAT cumplida en 4.9"


def test_02_update_qualitative_analysis():
    admin_headers = get_headers("admin", "superadmin")
    
    # Crear inicial
    client.post("/api/admin/clients/1/qualitative/2026-09", json={"critical_points": "Inicial"}, headers=admin_headers)

    # Actualizar
    res_update = client.put("/api/admin/clients/1/qualitative/2026-09", json={
        "critical_points": "Actualización Crítica",
        "warnings": "Nueva advertencia"
    }, headers=admin_headers)
    
    assert res_update.status_code == 200
    data = res_update.json()
    assert data["critical_points"] == "Actualización Crítica"
    assert data["warnings"] == "Nueva advertencia"


def test_03_operator_read_allowed_write_forbidden():
    op_headers = get_headers("operador", "operator")

    # Operador puede leer
    res_get = client.get("/api/admin/clients/1/qualitative/2026-09", headers=op_headers)
    assert res_get.status_code == 200

    # Operador no puede crear ni editar -> 403 Forbidden
    res_post = client.post("/api/admin/clients/1/qualitative/2026-09", json={"critical_points": "HACK"}, headers=op_headers)
    assert res_post.status_code == 403

    res_put = client.put("/api/admin/clients/1/qualitative/2026-09", json={"critical_points": "HACK"}, headers=op_headers)
    assert res_put.status_code == 403


def test_04_qualitative_analysis_in_public_view():
    admin_headers = get_headers("admin", "superadmin")
    
    # Guardar cualitativo como superadmin
    client.post("/api/admin/clients/1/qualitative/2026-09", json={
        "critical_points": "Punto crítico visible en link público",
        "achievements": "Logro visible públicamente"
    }, headers=admin_headers)

    # Consultar endpoint público
    res_public = client.get("/api/public/token-test-qualitative")
    assert res_public.status_code == 200
    pub_data = res_public.json()
    assert "qualitative_analyses" in pub_data
    assert "2026-09" in pub_data["qualitative_analyses"]
    assert pub_data["qualitative_analyses"]["2026-09"]["critical_points"] == "Punto crítico visible en link público"
