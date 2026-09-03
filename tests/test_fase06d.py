import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database import Base, get_db
from app.main import app
from app.models import Client, ReportImport, User
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
    c = Client(name="Cliente Ingestas Test", is_active=True)
    db.add(c)

    admin_u = User(username="admin_test", hashed_password=hash_password("pass"), role="superadmin", is_active=True)
    op_u = User(username="op_test", hashed_password=hash_password("pass"), role="operator", is_active=True)
    db.add(admin_u)
    db.add(op_u)

    db.commit()
    db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def get_headers(role="superadmin", username="admin_test"):
    token = create_access_token({"sub": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_01_process_import_syncs_monthly_reports():
    tsv_users = (
        "Link Conversación\tFecha Sesión\tHora Sesión\tId Sesión\tId canal\tId Contacto/Número\tHabló el Agente\tMensajes Usuario\tMensajes Bot\tMensajes Agente\tTipificación\n"
        "https://bm.com/c1\t2026-09-01\t10:00\tses_01\tWhatsApp\t+50688880001\t1\t5\t2\t4\tConsulta\n"
    ).encode("utf-8")

    # 1. Subir
    res = client.post(
        "/api/admin/imports/",
        headers=get_headers("operator", "op_test"),
        data={"client_id": 1, "source_code": "botmaker", "period": "2026-09"},
        files={"file": ("users-2026-09.tsv", tsv_users, "text/tab-separated-values")}
    )
    assert res.status_code == 201
    import_id = res.json()["id"]
    assert res.json()["status"] == "VALID"

    # 2. Procesar
    res_proc = client.post(f"/api/admin/imports/{import_id}/process", headers=get_headers("operator", "op_test"))
    assert res_proc.status_code == 200
    assert res_proc.json()["status"] == "PROCESSED"

    # 3. Verificar que se sincronizó en monthly_reports
    res_rep = client.get("/api/clients/1/reports?year=2026", headers=get_headers("operator", "op_test"))
    assert res_rep.status_code == 200
    reports = res_rep.json()
    assert len(reports) == 1
    assert reports[0]["chats"] == 1


def test_02_delete_import_superadmin_vs_operator():
    tsv = "ColA\tColB\nVal1\tVal2\n".encode("utf-8")
    res = client.post(
        "/api/admin/imports/",
        headers=get_headers("superadmin"),
        data={"client_id": 1, "source_code": "generic", "period": "2026-09"},
        files={"file": ("data.tsv", tsv, "text/tab-separated-values")}
    )
    import_id = res.json()["id"]

    # Operador intenta eliminar -> 403
    res_op_del = client.delete(f"/api/admin/imports/{import_id}", headers=get_headers("operator", "op_test"))
    assert res_op_del.status_code == 403

    # Superadmin elimina -> 200
    res_admin_del = client.delete(f"/api/admin/imports/{import_id}", headers=get_headers("superadmin"))
    assert res_admin_del.status_code == 200
    assert res_admin_del.json()["detail"] == "Importación eliminada correctamente"


def test_03_cleanup_duplicates():
    db = TestingSessionLocal()
    dup = ReportImport(
        client_id=1,
        source_code="botmaker",
        period="2026-09",
        original_filename="dup.tsv",
        storage_path="uploads/raw/dup.tsv",
        file_format="tsv",
        file_size=100,
        file_hash="1234567890abcdef",
        status="DUPLICATE",
        uploaded_by="op_test"
    )
    db.add(dup)
    db.commit()
    db.close()

    # Operador intenta limpiar -> 403
    res_op = client.delete("/api/admin/imports/duplicates", headers=get_headers("operator", "op_test"))
    assert res_op.status_code == 403

    # Superadmin limpia -> 200
    res_admin = client.delete("/api/admin/imports/duplicates", headers=get_headers("superadmin"))
    assert res_admin.status_code == 200
    assert res_admin.json()["deleted_count"] == 1
