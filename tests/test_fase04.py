import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database import Base, get_db
from app.main import app
from app.models import Client, ReportImport, KPIConfig, KPIResult, NormalizedRecord
from app.auth import create_access_token
from app.services.kpi_engine.formula_evaluator import FormulaEvaluator
from app.services.normalizer.yeastar_parsers import (
    YeastarExtensionStatsParser,
    YeastarExtensionActivityParser,
    YeastarQueuePerformanceParser
)

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

def create_sample_client(name="Cliente Fase 04"):
    db = TestingSessionLocal()
    c = Client(name=name, is_active=True)
    db.add(c)
    db.commit()
    c_id = c.id
    db.close()
    return c_id


# ── TEST 01: Create KPI Config ─────────────────────────────────────────
def test_01_create_kpi_config():
    c_id = create_sample_client()
    payload = {
        "kpi_code": "sla_citas",
        "kpi_name": "SLA de Citas",
        "source_code": "yeastar",
        "report_type": "queue",
        "target_value": 90.0,
        "formula_type": "ratio",
        "input_metrics": ["answered", "total"],
        "direction": "higher_is_better",
        "unit": "percentage"
    }

    res = client.post(f"/api/admin/kpis/clients/{c_id}", headers=get_admin_headers(), json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["kpi_code"] == "sla_citas"
    assert data["target_value"] == 90.0
    assert data["client_id"] == c_id


# ── TEST 02: Update KPI Config ─────────────────────────────────────────
def test_02_update_kpi_config():
    c_id = create_sample_client()
    res1 = client.post(
        f"/api/admin/kpis/clients/{c_id}",
        headers=get_admin_headers(),
        json={"kpi_code": "csat", "kpi_name": "CSAT Inicial", "target_value": 80.0}
    )
    k_id = res1.json()["id"]

    res2 = client.put(
        f"/api/admin/kpis/{k_id}",
        headers=get_admin_headers(),
        json={"target_value": 85.0, "description": "CSAT actualizado"}
    )
    assert res2.status_code == 200
    assert res2.json()["target_value"] == 85.0
    assert res2.json()["description"] == "CSAT actualizado"


# ── TEST 03: Toggle KPI Config ─────────────────────────────────────────
def test_03_toggle_kpi_config():
    c_id = create_sample_client()
    res1 = client.post(
        f"/api/admin/kpis/clients/{c_id}",
        headers=get_admin_headers(),
        json={"kpi_code": "temp_kpi", "kpi_name": "KPI Temporal"}
    )
    k_id = res1.json()["id"]

    res2 = client.delete(f"/api/admin/kpis/{k_id}", headers=get_admin_headers())
    assert res2.status_code == 200

    db = TestingSessionLocal()
    cfg = db.query(KPIConfig).filter(KPIConfig.id == k_id).first()
    db.close()
    assert cfg.is_active is False


# ── TEST 04: Different KPIs per client ─────────────────────────────────
def test_04_different_kpis_per_client():
    c1 = create_sample_client("Kidoz")
    c2 = create_sample_client("Petopia")

    client.post(f"/api/admin/kpis/clients/{c1}", headers=get_admin_headers(), json={"kpi_code": "kidoz_sales", "kpi_name": "Ventas Kidoz"})
    client.post(f"/api/admin/kpis/clients/{c2}", headers=get_admin_headers(), json={"kpi_code": "petopia_vol", "kpi_name": "Volumen Petopia"})

    res1 = client.get(f"/api/admin/kpis/clients/{c1}", headers=get_admin_headers())
    res2 = client.get(f"/api/admin/kpis/clients/{c2}", headers=get_admin_headers())

    assert len(res1.json()) == 1 and res1.json()[0]["kpi_code"] == "kidoz_sales"
    assert len(res2.json()) == 1 and res2.json()[0]["kpi_code"] == "petopia_vol"


# ── TEST 05: Formula Evaluator Ratio ──────────────────────────────────
def test_05_formula_evaluator_ratio():
    val, err = FormulaEvaluator.evaluate("ratio", {"answered": 1173, "total": 1327})
    assert err is None
    assert round(val, 2) == 88.39


# ── TEST 06: Formula Evaluator Difference ─────────────────────────────
def test_06_formula_evaluator_difference():
    val, err = FormulaEvaluator.evaluate("difference", {"actual": 100, "baseline": 80})
    assert err is None
    assert val == 20.0


# ── TEST 07: Formula Evaluator Percentage Gap ────────────────────────
def test_07_formula_evaluator_percentage_gap():
    val, err = FormulaEvaluator.evaluate("percentage_gap", {"actual": 120, "target": 100})
    assert err is None
    assert val == 20.0


# ── TEST 08: Formula Evaluator Zero Division ─────────────────────────
def test_08_formula_evaluator_zero_division():
    val, err = FormulaEvaluator.evaluate("ratio", {"answered": 100, "total": 0})
    assert val is None
    assert "División por cero" in err


# ── TEST 09: Formula Evaluator Invalid Type ───────────────────────────
def test_09_formula_evaluator_invalid_type():
    val, err = FormulaEvaluator.evaluate("invalida", {"a": 1})
    assert val is None
    assert "no soportado" in err


# ── TEST 10: Target Status Higher is Better ───────────────────────────
def test_10_target_status_higher_is_better():
    s1, color1 = FormulaEvaluator.determine_status(88.39, 90.0, "higher_is_better")
    assert s1 == "BELOW_TARGET" and color1 == "red"

    s2, color2 = FormulaEvaluator.determine_status(95.0, 90.0, "higher_is_better")
    assert s2 == "ON_TARGET" and color2 == "green"


# ── TEST 11: Target Status Lower is Better ────────────────────────────
def test_11_target_status_lower_is_better():
    s1, color1 = FormulaEvaluator.determine_status(11.61, 10.0, "lower_is_better")
    assert s1 == "ABOVE_TARGET" and color1 == "red"

    s2, color2 = FormulaEvaluator.determine_status(8.0, 10.0, "lower_is_better")
    assert s2 == "ON_TARGET" and color2 == "green"


# ── TEST 12: No Target Status ─────────────────────────────────────────
def test_12_no_target_status():
    status, color = FormulaEvaluator.determine_status(88.39, None, "higher_is_better")
    assert status == "NO_TARGET"
    assert color == "gray"


# ── TEST 13: NULL and NOT_AVAILABLE Handling ─────────────────────────
def test_13_null_and_not_available_handling():
    status, color = FormulaEvaluator.determine_status(None, 90.0, "higher_is_better")
    assert status == "NOT_AVAILABLE"
    assert color == "gray"


# ── TEST 14: Yeastar Extension Stats Parser ───────────────────────────
def test_14_yeastar_extension_stats_parser():
    parser = YeastarExtensionStatsParser()
    headers = ["Extensión", "Tipo de comunicación", "Contestada", "No Contestada", "Total", "Duración Total de Conversación"]
    row = ["1003-Magdelin Martínez", "Entrante", "14", "223", "237", "4058"]

    res = parser.parse_row(row, headers, row_number=2)
    assert res["agent"] == "1003-Magdelin Martínez"
    assert res["messages_count"] == 237
    assert res["duration_seconds"] == 4058.0


# ── TEST 15: Yeastar Extension Activity Parser ────────────────────────
def test_15_yeastar_extension_activity_parser():
    parser = YeastarExtensionActivityParser()
    headers = ["Mes", "Extensión", "Contestada", "Duración Total de Timbre", "Duración Total de Conversación"]
    row = ["04/2026", "1003-Magdelin Martínez", "14", "120", "4058"]

    res = parser.parse_row(row, headers, row_number=2)
    assert res["agent"] == "1003-Magdelin Martínez"
    assert res["normalized_data"]["month"] == "04/2026"
    assert res["wait_time_seconds"] == 120.0
    assert res["duration_seconds"] == 4058.0


# ── TEST 16: Yeastar Queue Performance Parser ─────────────────────────
def test_16_yeastar_queue_performance_parser():
    parser = YeastarQueuePerformanceParser()
    headers = ["Cola", "Periodo", "Llamadas Totales", "Contestada", "Abandonada", "AVG Handle Time", "AVG Wait", "SLA %"]
    row = ["6400-CITAS", "2026-08", "1327", "1173", "154", "122", "18", "84.02"]

    res = parser.parse_row(row, headers, row_number=2)
    assert res["queue"] == "6400-CITAS"
    assert res["messages_count"] == 1327
    assert res["normalized_data"]["answered"] == 1173
    assert res["normalized_data"]["abandoned"] == 154
    assert res["normalized_data"]["sla_percent"] == 84.02


# ── TEST 17: Calculate KPIs for Period ────────────────────────────────
def test_17_calculate_kpis_for_period():
    c_id = create_sample_client()

    # Crear configuración de KPI
    client.post(
        f"/api/admin/kpis/clients/{c_id}",
        headers=get_admin_headers(),
        json={
            "kpi_code": "tasa_contesta",
            "kpi_name": "Tasa de Contesta",
            "source_code": "yeastar",
            "target_value": 90.0,
            "formula_type": "ratio",
            "input_metrics": ["answered", "total"],
            "direction": "higher_is_better"
        }
    )

    # Calcular KPIs
    res = client.post(
        f"/api/admin/kpis/calculate?client_id={c_id}&period=2026-08",
        headers=get_admin_headers()
    )
    assert res.status_code == 200
    results = res.json()
    assert len(results) == 1
    assert results[0]["kpi_code"] == "tasa_contesta"


# ── TEST 18: KPI Traceability ─────────────────────────────────────────
def test_18_kpi_traceability():
    c_id = create_sample_client()

    res_cfg = client.post(
        f"/api/admin/kpis/clients/{c_id}",
        headers=get_admin_headers(),
        json={"kpi_code": "kpi_trazable", "kpi_name": "KPI Trazable", "target_value": 50.0}
    )

    client.post(f"/api/admin/kpis/calculate?client_id={c_id}&period=2026-08", headers=get_admin_headers())

    res_history = client.get(f"/api/admin/kpis/results?client_id={c_id}", headers=get_admin_headers())
    res_id = res_history.json()[0]["id"]

    res_trace = client.get(f"/api/admin/kpis/results/{res_id}/traceability", headers=get_admin_headers())
    assert res_trace.status_code == 200
    data = res_trace.json()
    assert data["kpi_code"] == "kpi_trazable"
    assert "traceability_info" in data


# ── TEST 19: Security Authorization ───────────────────────────────────
def test_19_security_authorization():
    res1 = client.get("/api/admin/kpis/clients/1")
    assert res1.status_code == 401

    res2 = client.post("/api/admin/kpis/calculate?client_id=1&period=2026-08")
    assert res2.status_code == 401


# ── TEST 20: Regression Fases 01, 02, 03 ──────────────────────────────
def test_20_regression_fases01_fase02_fase03():
    # Fase 01
    res_dash = client.get("/api/admin/dashboard-global", headers=get_admin_headers())
    assert res_dash.status_code == 200

    # Fase 02
    res_imp = client.get("/api/admin/imports/", headers=get_admin_headers())
    assert res_imp.status_code == 200
