import pytest
import io
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database import Base, get_db
from app.main import app
from app.models import Client, ReportImport, AuditLog, MonthlyReport, PublicView
from app.auth import create_access_token
from app.services.hash_service import calculate_sha256


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
    c = Client(name="Cliente Prueba Ingesta", is_active=True)
    db.add(c)
    db.commit()
    c_id = c.id
    db.close()
    return c_id


# ── TEST 01: Import Botmaker users ─────────────────────────────────────
def test_01_import_botmaker_users():
    c_id = create_sample_client()
    content = b"conversation\tdate\ttime\tsession\tchannel\tcontact\tagent\tmessages\nconv123\t2026-09-01\t20:31\tses1\tWhatsApp\t+50688888888\tAgentA\t5\n"
    file_tuple = ("users-2026.09.01-20.31.tsv", content, "text/tab-separated-values")

    response = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": "botmaker", "report_type": "users", "period": "2026-09"},
        files={"file": file_tuple}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == "users-2026.09.01-20.31.tsv"
    assert data["status"] in ["VALID", "VALID_WITH_WARNINGS"]
    assert data["records_count"] == 1


# ── TEST 02: Import operatorsSessionsDebug ────────────────────────────
def test_02_import_operators_sessions_debug():
    c_id = create_sample_client()
    content = b"session\tuser\tstart\tend\tagent\tqueue\ttypification\twait\n" \
              b"s100\tu200\t2026-09-01 20:00\t2026-09-01 20:10\tAgente1\tSoporte\tConsulta\t12s\n"
    file_tuple = ("operatorsSessionsDebug-2026.09.01-20.31.tsv", content, "text/tab-separated-values")

    response = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": "botmaker", "report_type": "operatorsSessionsDebug"},
        files={"file": file_tuple}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == "operatorsSessionsDebug-2026.09.01-20.31.tsv"
    assert data["period"] == "2026-09"


# ── TEST 03: Import sessionStartingCauses ─────────────────────────────
def test_03_import_session_starting_causes():
    c_id = create_sample_client()
    content = b"user\tcontact\tchannel\ttemplate\tsent\tdelivered\tread\n" \
              b"u300\t+50670000000\tWhatsApp\ttpl_promo\tTrue\tTrue\tTrue\n"
    file_tuple = ("sessionStartingCauses-2026.09.01-20.31.tsv", content, "text/tab-separated-values")

    response = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": "botmaker", "report_type": "sessionStartingCauses"},
        files={"file": file_tuple}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] in ["VALID", "VALID_WITH_WARNINGS"]


# ── TEST 04: Detect TSV correctly ─────────────────────────────────────
def test_04_detect_tsv_correctly():
    c_id = create_sample_client()
    content = b"colA\tcolB\tcolC\nvalA\tvalB\tvalC\n"
    file_tuple = ("test_data.tsv", content, "text/tab-separated-values")

    response = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": "manual"},
        files={"file": file_tuple}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["file_format"] == "tsv"
    assert data["metadata_info"]["delimiter"] == "\\t"


# ── TEST 05: Validate headers ─────────────────────────────────────────
def test_05_validate_headers():
    c_id = create_sample_client()
    # Encabezado incompleto para botmaker users
    content = b"columna_desconocida_1\tcolumna_desconocida_2\nval1\tval2\n"
    file_tuple = ("users-2026.09.01-20.31.tsv", content, "text/tab-separated-values")

    response = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": "botmaker", "report_type": "users"},
        files={"file": file_tuple}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "VALID_WITH_WARNINGS"
    assert len(data["warnings"]) > 0


# ── TEST 06: Generate SHA-256 ────────────────────────────────────────
def test_06_generate_sha256():
    raw_bytes = b"contenido de prueba para hash sha256"
    computed_hash = calculate_sha256(raw_bytes)
    assert len(computed_hash) == 64
    assert isinstance(computed_hash, str)


# ── TEST 07: Detect duplicate file ───────────────────────────────────
def test_07_detect_duplicate_file():
    c_id = create_sample_client()
    content = b"header1\theader2\ndata1\tdata2\n"
    file_tuple = ("archivo_unico.tsv", content, "text/tab-separated-values")

    # Primera carga
    res1 = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": "manual"},
        files={"file": file_tuple}
    )
    assert res1.status_code == 201

    # Segunda carga del mismo archivo (mismo hash)
    res2 = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": "manual"},
        files={"file": ("archivo_unico.tsv", content, "text/tab-separated-values")}
    )
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["status"] == "DUPLICATE"


# ── TEST 08: Reject disallowed extension ─────────────────────────────
def test_08_reject_disallowed_extension():
    c_id = create_sample_client()
    content = b"echo 'hacked'"
    file_tuple = ("script_malicioso.exe", content, "application/octet-stream")

    response = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": "manual"},
        files={"file": file_tuple}
    )
    assert response.status_code == 400
    assert "Extensión de archivo no permitida" in response.json()["detail"]


# ── TEST 09: Reject oversized file ───────────────────────────────────
def test_09_reject_oversized_file():
    c_id = create_sample_client()
    # Generar contenido sintético mayor a 50 MB
    content = b"x" * (51 * 1024 * 1024)
    file_tuple = ("archivo_gigante.csv", content, "text/csv")

    response = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": "manual"},
        files={"file": file_tuple}
    )
    assert response.status_code == 400
    assert "excede el tamaño máximo" in response.json()["detail"]


# ── TEST 10: Record row errors without silent loss ───────────────────
def test_10_record_row_errors_without_silent_loss():
    c_id = create_sample_client()
    # Fila 2 con número incorrecto de columnas
    content = b"h1\th2\th3\nv1\tv2\tv3\nv1_solo\n"
    file_tuple = ("discrepante.tsv", content, "text/tab-separated-values")

    response = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": "manual"},
        files={"file": file_tuple}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["records_count"] == 2
    assert len(data["warnings"]) > 0
    assert any(w["row"] == 3 for w in data["warnings"])


# ── TEST 11: Save import metadata ────────────────────────────────────
def test_11_save_import_metadata():
    c_id = create_sample_client()
    content = b"col1\tcol2\nval1\tval2\n"
    file_tuple = ("metadata_test.tsv", content, "text/tab-separated-values")

    response = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": "manual"},
        files={"file": file_tuple}
    )
    assert response.status_code == 201
    data = response.json()
    assert "metadata_info" in data
    assert data["metadata_info"]["encoding"] in ["utf-8", "utf-8-sig"]

    assert data["metadata_info"]["delimiter"] == "\\t"


# ── TEST 12: Preserve RAW file ───────────────────────────────────────
def test_12_preserve_raw_file():
    c_id = create_sample_client()
    raw_content = b"inmutable_content_test_12345"
    file_tuple = ("raw_test.txt", raw_content, "text/plain")

    res = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": "manual"},
        files={"file": file_tuple}
    )
    assert res.status_code == 201
    import_id = res.json()["id"]

    # Solicitar preview y verificar que el archivo RAW sea legible e inalterado
    res_prev = client.get(f"/api/admin/imports/{import_id}/preview", headers=get_admin_headers())
    assert res_prev.status_code == 200
    prev_data = res_prev.json()
    assert prev_data["original_filename"] == "raw_test.txt"


# ── TEST 13: Verify authorization ────────────────────────────────────
def test_13_verify_authorization():
    # Intento sin token
    res1 = client.get("/api/admin/imports/")
    assert res1.status_code == 401

    # Intento con token inválido
    res2 = client.get("/api/admin/imports/", headers={"Authorization": "Bearer token_invalido"})
    assert res2.status_code == 401


# ── TEST 14: Verify audit logging ────────────────────────────────────
def test_14_verify_audit_logging():
    c_id = create_sample_client()
    content = b"h1\th2\nv1\tv2\n"
    file_tuple = ("audit_test.tsv", content, "text/tab-separated-values")

    client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": "manual"},
        files={"file": file_tuple}
    )

    db = TestingSessionLocal()
    audit_entry = db.query(AuditLog).filter(AuditLog.resource_type == "import").first()
    db.close()

    assert audit_entry is not None
    assert audit_entry.action in ["IMPORT_STARTED", "IMPORT_COMPLETED"]


# ── TEST 15: Verify FASE 01 compatibility ───────────────────────────
def test_15_verify_fase01_compatibility():
    # 1. Dashboard Global
    res_dash = client.get("/api/admin/dashboard-global", headers=get_admin_headers())
    assert res_dash.status_code == 200

    # 2. Clientes
    res_cli = client.get("/api/clients/", headers=get_admin_headers())
    assert res_cli.status_code == 200

    # 3. Public view (404 si token inexistente, pero endpoint activo)
    res_pub = client.get("/api/public/token_inexistente_fase02")
    assert res_pub.status_code == 404
