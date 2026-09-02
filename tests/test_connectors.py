import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database import Base, get_db
from app.main import app
from app.models import Client, ReportImport
from app.auth import create_access_token
from app.services.connectors.botmaker_connector import BotmakerConnector
from app.services.connectors.yeastar_connector import YeastarConnector

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

def create_sample_client():
    db = TestingSessionLocal()
    c = Client(name="Cliente API Sync Test", is_active=True)
    db.add(c)
    db.commit()
    c_id = c.id
    db.close()
    return c_id


def test_01_botmaker_connector_sync():
    c_id = create_sample_client()
    db = TestingSessionLocal()
    connector = BotmakerConnector()
    import_rec = connector.sync_client_data(db, c_id, "2026-08")
    db.close()

    assert import_rec.id is not None
    assert import_rec.source_code == "botmaker"
    assert import_rec.period == "2026-08"
    assert import_rec.status in ["PROCESSED", "PROCESSED_WITH_WARNINGS"]


def test_02_yeastar_connector_sync():
    c_id = create_sample_client()
    db = TestingSessionLocal()
    connector = YeastarConnector()
    import_rec = connector.sync_queue_performance(db, c_id, "2026-08")
    db.close()

    assert import_rec.id is not None
    assert import_rec.source_code == "yeastar"
    assert import_rec.period == "2026-08"
    assert import_rec.status in ["PROCESSED", "PROCESSED_WITH_WARNINGS"]



def test_03_botmaker_sync_endpoint():
    c_id = create_sample_client()
    res = client.post(
        f"/api/admin/connectors/botmaker/sync?client_id={c_id}&period=2026-08",
        headers=get_admin_headers()
    )
    assert res.status_code == 200
    data = res.json()
    assert data["source_code"] == "botmaker"
    assert data["period"] == "2026-08"


def test_04_yeastar_sync_endpoint():
    c_id = create_sample_client()
    res = client.post(
        f"/api/admin/connectors/yeastar/sync?client_id={c_id}&period=2026-08",
        headers=get_admin_headers()
    )
    assert res.status_code == 200
    data = res.json()
    assert data["source_code"] == "yeastar"
    assert data["period"] == "2026-08"


def test_05_connectors_status_endpoint():
    res = client.get("/api/admin/connectors/status", headers=get_admin_headers())
    assert res.status_code == 200
    data = res.json()
    assert "botmaker_connector" in data
    assert "yeastar_connector" in data
