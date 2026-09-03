import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.auth import create_access_token


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
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

def get_admin_headers():
    token = create_access_token({"sub": "admin", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


def test_01_create_client_with_full_technical_datasheet():
    payload = {
        "name": "Clínica Kidoz Internacional",
        "description": "Cliente principal de pediatría y odontología",
        "color": "#009688",
        "logo_text": "KID",
        "contact_name": "Dra. María Fernández",
        "contact_email": "maria@clinicakidoz.com",
        "contact_phone": "+506 8888-9999",
        "industry": "Salud & Clínicas",
        "country": "Costa Rica",
        "has_botmaker": True,
        "botmaker_channel_id": "kidoz_whatsapp_prod",
        "has_yeastar": True,
        "yeastar_pbx_ip": "pbx.kidoz.cloud",
        "yeastar_extensions_count": 25,
        "sla_target_minutes": 3.5,
        "technical_notes": "Atención prioritaria 24/7 con integración Yeastar PBX v2",
        "platform_metadata": {"queues": ["general", "citas"], "webhook_enabled": True},
        "kpi_modules": ["chat_sales", "appointments", "calls", "quality_kidoz"]
    }
    res = client.post("/api/clients/", json=payload, headers=get_admin_headers())
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Clínica Kidoz Internacional"
    assert data["contact_name"] == "Dra. María Fernández"
    assert data["has_botmaker"] is True
    assert data["has_yeastar"] is True
    assert data["yeastar_extensions_count"] == 25
    assert data["sla_target_minutes"] == 3.5
    assert data["platform_metadata"]["webhook_enabled"] is True


def test_02_update_client_technical_datasheet():
    create_res = client.post("/api/clients/", json={
        "name": "Petopia Vet Center",
        "industry": "Veterinaria"
    }, headers=get_admin_headers())
    assert create_res.status_code == 201
    client_id = create_res.json()["id"]

    update_payload = {
        "contact_name": "Dr. Carlos Rojas",
        "contact_phone": "+506 7777-6666",
        "has_yeastar": True,
        "yeastar_extensions_count": 10,
        "sla_target_minutes": 4.0,
        "technical_notes": "Actualización de servidor Yeastar VoIP",
        "platform_metadata": {"cloud_region": "us-east-1"}
    }
    res = client.put(f"/api/clients/{client_id}", json=update_payload, headers=get_admin_headers())
    assert res.status_code == 200
    data = res.json()
    assert data["contact_name"] == "Dr. Carlos Rojas"
    assert data["has_yeastar"] is True
    assert data["yeastar_extensions_count"] == 10
    assert data["sla_target_minutes"] == 4.0
    assert data["platform_metadata"]["cloud_region"] == "us-east-1"


def test_03_get_client_technical_datasheet():
    create_res = client.post("/api/clients/", json={
        "name": "Farmacia Central",
        "country": "Panamá",
        "has_botmaker": True
    }, headers=get_admin_headers())
    assert create_res.status_code == 201
    client_id = create_res.json()["id"]

    res = client.get(f"/api/clients/{client_id}", headers=get_admin_headers())
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Farmacia Central"
    assert data["country"] == "Panamá"
    assert data["has_botmaker"] is True
