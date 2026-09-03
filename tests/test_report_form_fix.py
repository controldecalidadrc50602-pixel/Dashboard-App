import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database import Base, get_db
from app.main import app
from app.models import Client, MonthlyReport, User
from app.auth import create_access_token, hash_password

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

    # Cliente Botmaker
    c1 = Client(name="Cliente Kidoz", has_botmaker=True, has_yeastar=False, is_active=True)
    db.add(c1)

    # Cliente Híbrido
    c2 = Client(name="Cliente Petopia", has_botmaker=True, has_yeastar=True, is_active=True)
    db.add(c2)

    db.commit()

    # Reporte existente Septiembre 2026 para Kidoz
    r1 = MonthlyReport(
        client_id=c1.id,
        year=2026,
        month=9,
        chats=85,
        support=84,
        leads=20,
        sales=5,
        csat=4.8,
        extra_data={
            "botmaker": {
                "total_conversations": 85,
                "conversations_with_agent": 84,
                "conversations_bot_only": 1,
                "total_messages_user": 400,
                "total_messages_bot": 200,
                "total_messages_agent": 350
            }
        }
    )
    db.add(r1)
    db.commit()
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def get_headers():
    token = create_access_token({"sub": "admin", "role": "superadmin"})
    return {"Authorization": f"Bearer {token}"}


def test_01_get_report_by_period():
    res = client.get("/api/clients/1/reports/2026/9", headers=get_headers())
    assert res.status_code == 200
    data = res.json()
    assert data["chats"] == 85
    assert data["support"] == 84
    assert data["extra_data"]["botmaker"]["total_conversations"] == 85


def test_02_update_report_form_data():
    # Obtener el ID del reporte
    res_list = client.get("/api/clients/1/reports?year=2026", headers=get_headers())
    rep_id = res_list.json()[0]["id"]

    # Actualizar via PUT
    put_body = {
        "year": 2026,
        "month": 9,
        "chats": 100,
        "support": 90,
        "leads": 25,
        "sales": 10,
        "csat": 4.9,
        "extra_data": {
            "botmaker": {
                "total_conversations": 100,
                "conversations_with_agent": 90,
                "conversations_bot_only": 10,
                "total_messages_user": 500,
                "total_messages_bot": 250,
                "total_messages_agent": 400
            }
        }
    }

    res_put = client.put(f"/api/clients/1/reports/{rep_id}", headers=get_headers(), json=put_body)
    assert res_put.status_code == 200
    updated = res_put.json()
    assert updated["chats"] == 100
    assert updated["support"] == 90
    assert updated["sales"] == 10
