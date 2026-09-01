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
from app.models import Client, ReportImport, NormalizedRecord, AuditLog
from app.auth import create_access_token
from app.services.normalizer.base_parser import BaseParser
from app.services.normalizer.botmaker_users_parser import BotmakerUsersParser
from app.services.normalizer.botmaker_operators_parser import BotmakerOperatorsParser
from app.services.normalizer.botmaker_sessions_parser import BotmakerSessionsParser

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
    c = Client(name="Cliente Prueba Fase 03", is_active=True)
    db.add(c)
    db.commit()
    c_id = c.id
    db.close()
    return c_id

def upload_sample_import(c_id, source_code="botmaker", report_type="users", filename="users-2026.09.01-20.31.tsv", content=b"conversation\tdate\ttime\tsession\tchannel\tcontact\tagent\tmessages\nconv100\t2026-09-01\t20:31\tses100\tWhatsApp\t+50688888888\tAgentX\t4\n"):
    file_tuple = (filename, content, "text/tab-separated-values")
    res = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": c_id, "source_code": source_code, "report_type": report_type, "period": "2026-09"},
        files={"file": file_tuple}
    )
    return res.json()["id"]


# ── TEST 01: Parse Botmaker users ─────────────────────────────────────
def test_01_parse_botmaker_users():
    parser = BotmakerUsersParser()
    headers = ["conversation", "date", "time", "channel", "contact", "agent", "messages"]
    row = ["c123", "2026-09-01", "10:00", "WhatsApp", "+50688888888", "Carlos", "5"]
    
    result = parser.parse_row(row, headers, row_number=2)
    assert result["event_id"] == "c123"
    assert result["user_id"] == "+50688888888"
    assert result["channel"] == "WhatsApp"
    assert result["agent"] == "Carlos"
    assert result["messages_count"] == 5
    assert result["parser_version"] == "botmaker-users-v1.0"


# ── TEST 02: Parse operatorsSessionsDebug ────────────────────────────
def test_02_parse_operators_sessions_debug():
    parser = BotmakerOperatorsParser()
    headers = ["session", "user", "start", "end", "agent", "queue", "wait"]
    row = ["s555", "u777", "2026-09-01 10:00:00", "2026-09-01 10:15:00", "Maria", "Ventas", "30s"]

    result = parser.parse_row(row, headers, row_number=3)
    assert result["event_id"] == "s555"
    assert result["user_id"] == "u777"
    assert result["agent"] == "Maria"
    assert result["queue"] == "Ventas"
    assert result["wait_time_seconds"] == 30.0
    assert result["duration_seconds"] == 900.0


# ── TEST 03: Parse sessionStartingCauses ─────────────────────────────
def test_03_parse_session_starting_causes():
    parser = BotmakerSessionsParser()
    headers = ["user", "channel", "template", "responded", "timestamp"]
    row = ["+50670000000", "WhatsApp", "tpl_promocion", "True", "2026-09-01 12:00:00"]

    result = parser.parse_row(row, headers, row_number=4)
    assert result["user_id"] == "+50670000000"
    assert result["channel"] == "WhatsApp"
    assert result["typification"] == "tpl_promocion"
    assert result["is_abandoned"] is False


# ── TEST 04: Normalize records structure ─────────────────────────────
def test_04_normalize_records_structure():
    c_id = create_sample_client()
    imp_id = upload_sample_import(c_id)

    res = client.post(f"/api/admin/imports/{imp_id}/process", headers=get_admin_headers())
    assert res.status_code == 200
    data = res.json()
    assert data["total_rows_processed"] == 1
    assert data["status"] in ["PROCESSED", "PROCESSED_WITH_WARNINGS"]


# ── TEST 05: Maintain client_id ──────────────────────────────────────
def test_05_maintain_client_id():
    c_id = create_sample_client()
    imp_id = upload_sample_import(c_id)
    client.post(f"/api/admin/imports/{imp_id}/process", headers=get_admin_headers())

    db = TestingSessionLocal()
    rec = db.query(NormalizedRecord).filter(NormalizedRecord.import_id == imp_id).first()
    db.close()

    assert rec is not None
    assert rec.client_id == c_id


# ── TEST 06: Maintain import_id ──────────────────────────────────────
def test_06_maintain_import_id():
    c_id = create_sample_client()
    imp_id = upload_sample_import(c_id)
    client.post(f"/api/admin/imports/{imp_id}/process", headers=get_admin_headers())

    db = TestingSessionLocal()
    rec = db.query(NormalizedRecord).filter(NormalizedRecord.import_id == imp_id).first()
    db.close()

    assert rec is not None
    assert rec.import_id == imp_id


# ── TEST 07: Maintain raw reference ──────────────────────────────────
def test_07_maintain_raw_reference():
    c_id = create_sample_client()
    imp_id = upload_sample_import(c_id)
    client.post(f"/api/admin/imports/{imp_id}/process", headers=get_admin_headers())

    db = TestingSessionLocal()
    rec = db.query(NormalizedRecord).filter(NormalizedRecord.import_id == imp_id).first()
    db.close()

    assert rec.row_number == 2
    assert "conv100" in str(rec.raw_data)


# ── TEST 08: Handle missing fields as NULL ────────────────────────────
def test_08_handle_missing_fields_as_null():
    parser = BotmakerUsersParser()
    headers = ["conversation", "messages"]
    row = ["conv_vacia", ""]

    result = parser.parse_row(row, headers, row_number=2)
    assert result["messages_count"] is None
    assert result["messages_count"] != 0
    assert result["agent"] is None


# ── TEST 09: Differentiate NULL from zero ────────────────────────────
def test_09_differentiate_null_from_zero():
    assert BaseParser.parse_int("") is None
    assert BaseParser.parse_int("N/A") is None
    assert BaseParser.parse_int("-") is None
    assert BaseParser.parse_int("0") == 0
    assert BaseParser.parse_int("0") is not None


# ── TEST 10: Handle valid datetimes ──────────────────────────────────
def test_10_handle_valid_datetimes():
    dt1 = BaseParser.parse_datetime("2026-09-01 15:30:00")
    assert dt1 is not None
    assert dt1.year == 2026 and dt1.month == 9 and dt1.day == 1

    dt2 = BaseParser.parse_datetime("01/09/2026 15:30")
    assert dt2 is not None
    assert dt2.day == 1 and dt2.month == 9


# ── TEST 11: Handle invalid datetimes ────────────────────────────────
def test_11_handle_invalid_datetimes():
    dt = BaseParser.parse_datetime("fecha_invalida_123")
    assert dt is None


# ── TEST 12: Handle invalid numeric values ───────────────────────────
def test_12_handle_invalid_numeric_values():
    assert BaseParser.parse_float("invalido") is None
    assert BaseParser.parse_duration_seconds("error_time") is None
    assert BaseParser.parse_bool("no_booleano") is None


# ── TEST 13: Avoid normalized duplication ────────────────────────────
def test_13_avoid_normalized_duplication():
    c_id = create_sample_client()
    imp_id = upload_sample_import(c_id)

    # Primer procesamiento
    client.post(f"/api/admin/imports/{imp_id}/process", headers=get_admin_headers())
    db = TestingSessionLocal()
    count1 = db.query(NormalizedRecord).filter(NormalizedRecord.import_id == imp_id).count()
    db.close()
    assert count1 == 1

    # Reprocesamiento
    client.post(f"/api/admin/imports/{imp_id}/process", headers=get_admin_headers())
    db = TestingSessionLocal()
    count2 = db.query(NormalizedRecord).filter(NormalizedRecord.import_id == imp_id).count()
    db.close()
    assert count2 == 1  # No se duplicaron registros


# ── TEST 14: Reprocess RAW file ───────────────────────────────────────
def test_14_reprocess_raw_file():
    c_id = create_sample_client()
    imp_id = upload_sample_import(c_id)

    res = client.post(f"/api/admin/imports/{imp_id}/process", headers=get_admin_headers())
    assert res.status_code == 200

    # Obtener resumen
    res_summary = client.get(f"/api/admin/imports/{imp_id}/normalized-summary", headers=get_admin_headers())
    assert res_summary.status_code == 200
    data = res_summary.json()
    assert data["summary"]["total_records"] == 1


# ── TEST 15: Track parser version ─────────────────────────────────────
def test_15_track_parser_version():
    c_id = create_sample_client()
    imp_id = upload_sample_import(c_id, source_code="botmaker", report_type="users")
    client.post(f"/api/admin/imports/{imp_id}/process", headers=get_admin_headers())

    db = TestingSessionLocal()
    rec = db.query(NormalizedRecord).filter(NormalizedRecord.import_id == imp_id).first()
    db.close()

    assert rec.parser_version == "botmaker-users-v1.0"


# ── TEST 16: Verify traceability endpoint ─────────────────────────────
def test_16_verify_traceability_endpoint():
    c_id = create_sample_client()
    imp_id = upload_sample_import(c_id)
    client.post(f"/api/admin/imports/{imp_id}/process", headers=get_admin_headers())

    res = client.get(f"/api/admin/imports/{imp_id}/quality", headers=get_admin_headers())
    assert res.status_code == 200
    data = res.json()
    assert "sample_traceability" in data
    assert len(data["sample_traceability"]) == 1
    assert data["sample_traceability"][0]["row_number"] == 2


# ── TEST 17: Verify security authorization ───────────────────────────
def test_17_verify_security_authorization():
    res1 = client.post("/api/admin/imports/1/process")
    assert res1.status_code == 401

    res2 = client.get("/api/admin/imports/1/normalized-summary")
    assert res2.status_code == 401


# ── TEST 18: Verify Fase 01 and Fase 02 compatibility ─────────────────
def test_18_verify_fase01_and_fase02_compatibility():
    # Endpoint Fase 01
    res_dash = client.get("/api/admin/dashboard-global", headers=get_admin_headers())
    assert res_dash.status_code == 200

    # Endpoint Fase 02
    res_imp = client.get("/api/admin/imports/", headers=get_admin_headers())
    assert res_imp.status_code == 200
