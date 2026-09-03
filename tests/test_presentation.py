import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Client, MonthlyReport, ReportQualitativeAnalysis
from app.auth import create_access_token
from app.services.presentation_service import generate_pptx_presentation

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

    c1 = Client(name="Empresa Test PPTX", has_botmaker=True, has_yeastar=True, is_active=True)
    db.add(c1)
    db.commit()

    r1 = MonthlyReport(
        client_id=c1.id,
        year=2026,
        month=9,
        chats=120,
        support=95,
        leads=30,
        sales=12,
        csat=4.9
    )
    db.add(r1)

    q1 = ReportQualitativeAnalysis(
        client_id=c1.id,
        period="2026-09",
        critical_points="Punto crítico de prueba",
        warnings="Advertencia de prueba",
        achievements="Logro destacado",
        general_info="Info general"
    )
    db.add(q1)

    db.commit()
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def get_headers():
    token = create_access_token({"sub": "admin", "role": "superadmin"})
    return {"Authorization": f"Bearer {token}"}


def test_01_generate_pptx_bytes():
    stream = generate_pptx_presentation(
        client_name="Cliente Demostración",
        period="2026-09",
        theme="teal",
        num_slides=5,
        sections=["resumen", "eficiencia", "qualitative"],
        kpi_metrics={"chats": 100, "leads": 20, "sales": 5, "csat": 4.8},
        qualitative_data={"critical_points": "Atención requerida"}
    )
    assert stream is not None
    data_bytes = stream.getvalue()
    assert len(data_bytes) > 1000
    assert data_bytes.startswith(b"PK")  # Cabecera de archivo ZIP / PPTX


def test_02_post_presentation_endpoint():
    payload = {
        "period": "2026-09",
        "theme": "blue",
        "num_slides": 4,
        "sections": ["resumen", "qualitative"]
    }
    response = client.post("/api/admin/clients/1/presentation", headers=get_headers(), json=payload)
    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.presentationml.presentation" in response.headers["content-type"]
    assert "attachment; filename=" in response.headers.get("content-disposition", "")
    assert len(response.content) > 1000
    assert response.content.startswith(b"PK")
