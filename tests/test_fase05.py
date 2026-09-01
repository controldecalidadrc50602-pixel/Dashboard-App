import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database import Base, get_db
from app.main import app
from app.models import Client, ReportImport, KPIConfig, KPIResult, AnalysisInsight
from app.auth import create_access_token
from app.services.analysis_engine.analysis_service import run_rc506_analysis, get_previous_period_str
from app.services.analysis_engine.rules_registry import RC506RulesRegistry

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

def create_sample_client(name="Cliente Fase 05"):
    db = TestingSessionLocal()
    c = Client(name=name, is_active=True)
    db.add(c)
    db.commit()
    c_id = c.id
    db.close()
    return c_id

def create_sample_kpi_and_result(c_id, period="2026-08", value=88.39, target=90.0, status="BELOW_TARGET"):
    db = TestingSessionLocal()
    cfg = KPIConfig(
        client_id=c_id,
        kpi_code="sla_citas",
        kpi_name="SLA de Citas",
        source_code="yeastar",
        target_value=target,
        formula_type="ratio",
        direction="higher_is_better"
    )
    db.add(cfg)
    db.commit()

    res = KPIResult(
        client_id=c_id,
        kpi_config_id=cfg.id,
        period=period,
        kpi_code="sla_citas",
        source_code="yeastar",
        value=value,
        target_value=target,
        status=status,
        status_color="red" if status == "BELOW_TARGET" else "green",
        formula_used="ratio",
        input_values={"answered": 1173, "total": 1327}
    )
    db.add(res)
    db.commit()
    cfg_id, res_id = cfg.id, res.id
    db.close()
    return cfg_id, res_id


# ── TEST 01: Target Compliance ON_TARGET ──────────────────────────────
def test_01_target_compliance_on_target():
    c_id = create_sample_client()
    create_sample_kpi_and_result(c_id, value=95.0, target=90.0, status="ON_TARGET")

    db = TestingSessionLocal()
    insights = run_rc506_analysis(db, c_id, "2026-08")
    db.close()

    assert len(insights) >= 1
    tc_insight = next(i for i in insights if i.analysis_type == "TARGET_COMPLIANCE")
    assert tc_insight.severity == "POSITIVE"
    assert "Meta Alcanzada" in tc_insight.title


# ── TEST 02: Target Compliance BELOW_TARGET ───────────────────────────
def test_02_target_compliance_below_target():
    c_id = create_sample_client()
    create_sample_kpi_and_result(c_id, value=84.02, target=90.0, status="BELOW_TARGET")

    db = TestingSessionLocal()
    insights = run_rc506_analysis(db, c_id, "2026-08")
    db.close()

    assert len(insights) >= 1
    tc_insight = next(i for i in insights if i.analysis_type == "TARGET_COMPLIANCE")
    assert tc_insight.severity in ["WARNING", "CRITICAL"]
    assert "Desviación" in tc_insight.title


# ── TEST 03: Target Compliance NO_TARGET ──────────────────────────────
def test_03_target_compliance_no_target():
    c_id = create_sample_client()
    create_sample_kpi_and_result(c_id, value=88.0, target=None, status="NO_TARGET")

    db = TestingSessionLocal()
    insights = run_rc506_analysis(db, c_id, "2026-08")
    db.close()

    tc_insight = next(i for i in insights if i.analysis_type == "TARGET_COMPLIANCE")
    assert tc_insight.severity == "INFO"
    assert "sin Meta" in tc_insight.title


# ── TEST 04: Period over Period Improvement ────────────────────────────
def test_04_period_over_period_improvement():
    c_id = create_sample_client()

    db = TestingSessionLocal()
    cfg = KPIConfig(client_id=c_id, kpi_code="sla", kpi_name="SLA", direction="higher_is_better")
    db.add(cfg)
    db.commit()

    # Período anterior (Julio)
    res_jul = KPIResult(client_id=c_id, kpi_config_id=cfg.id, period="2026-07", kpi_code="sla", source_code="yeastar", value=80.0)
    # Período actual (Agosto)
    res_aug = KPIResult(client_id=c_id, kpi_config_id=cfg.id, period="2026-08", kpi_code="sla", source_code="yeastar", value=88.0, status="ON_TARGET")
    db.add_all([res_jul, res_aug])
    db.commit()

    insights = run_rc506_analysis(db, c_id, "2026-08")
    db.close()

    pop_insight = next(i for i in insights if i.analysis_type == "PERIOD_OVER_PERIOD")
    assert pop_insight.severity == "POSITIVE"
    assert pop_insight.delta == 8.0


# ── TEST 05: Period over Period Decline ────────────────────────────────
def test_05_period_over_period_decline():
    c_id = create_sample_client()

    db = TestingSessionLocal()
    cfg = KPIConfig(client_id=c_id, kpi_code="sla", kpi_name="SLA", direction="higher_is_better")
    db.add(cfg)
    db.commit()

    res_jul = KPIResult(client_id=c_id, kpi_config_id=cfg.id, period="2026-07", kpi_code="sla", source_code="yeastar", value=92.0)
    res_aug = KPIResult(client_id=c_id, kpi_config_id=cfg.id, period="2026-08", kpi_code="sla", source_code="yeastar", value=84.0, status="BELOW_TARGET", target_value=90.0)
    db.add_all([res_jul, res_aug])
    db.commit()

    insights = run_rc506_analysis(db, c_id, "2026-08")
    db.close()

    pop_insight = next(i for i in insights if i.analysis_type == "PERIOD_OVER_PERIOD")
    assert pop_insight.severity in ["WARNING", "CRITICAL"]
    assert pop_insight.delta == -8.0


# ── TEST 06: Period over Period No Previous ────────────────────────────
def test_06_period_over_period_no_previous():
    c_id = create_sample_client()
    create_sample_kpi_and_result(c_id, period="2026-08")

    db = TestingSessionLocal()
    insights = run_rc506_analysis(db, c_id, "2026-08")
    db.close()

    pop_insights = [i for i in insights if i.analysis_type == "PERIOD_OVER_PERIOD"]
    assert len(pop_insights) == 0


# ── TEST 07: Trend Improving ─────────────────────────────────────────
def test_07_trend_improving():
    c_id = create_sample_client()

    db = TestingSessionLocal()
    cfg = KPIConfig(client_id=c_id, kpi_code="csat", kpi_name="CSAT", direction="higher_is_better")
    db.add(cfg)
    db.commit()

    r1 = KPIResult(client_id=c_id, kpi_config_id=cfg.id, period="2026-06", kpi_code="csat", source_code="b", value=75.0)
    r2 = KPIResult(client_id=c_id, kpi_config_id=cfg.id, period="2026-07", kpi_code="csat", source_code="b", value=80.0)
    r3 = KPIResult(client_id=c_id, kpi_config_id=cfg.id, period="2026-08", kpi_code="csat", source_code="b", value=88.0, status="ON_TARGET")
    db.add_all([r1, r2, r3])
    db.commit()

    insights = run_rc506_analysis(db, c_id, "2026-08")
    db.close()

    trend_insight = next(i for i in insights if i.analysis_type == "TREND")
    assert trend_insight.severity == "POSITIVE"
    assert "IMPROVING" in trend_insight.title


# ── TEST 08: Trend Declining ─────────────────────────────────────────
def test_08_trend_declining():
    c_id = create_sample_client()

    db = TestingSessionLocal()
    cfg = KPIConfig(client_id=c_id, kpi_code="csat", kpi_name="CSAT", direction="higher_is_better")
    db.add(cfg)
    db.commit()

    r1 = KPIResult(client_id=c_id, kpi_config_id=cfg.id, period="2026-06", kpi_code="csat", source_code="b", value=90.0)
    r2 = KPIResult(client_id=c_id, kpi_config_id=cfg.id, period="2026-07", kpi_code="csat", source_code="b", value=82.0)
    r3 = KPIResult(client_id=c_id, kpi_config_id=cfg.id, period="2026-08", kpi_code="csat", source_code="b", value=74.0, status="BELOW_TARGET")
    db.add_all([r1, r2, r3])
    db.commit()

    insights = run_rc506_analysis(db, c_id, "2026-08")
    db.close()

    trend_insight = next(i for i in insights if i.analysis_type == "TREND")
    assert trend_insight.severity in ["WARNING", "CRITICAL"]
    assert "DECLINING" in trend_insight.title


# ── TEST 09: Trend Insufficient Data ─────────────────────────────────
def test_09_trend_insufficient_data():
    c_id = create_sample_client()
    create_sample_kpi_and_result(c_id, period="2026-08")

    db = TestingSessionLocal()
    insights = run_rc506_analysis(db, c_id, "2026-08")
    db.close()

    trend_insights = [i for i in insights if i.analysis_type == "TREND"]
    assert len(trend_insights) == 0


# ── TEST 10: Data Quality Missing Data ───────────────────────────────
def test_10_data_quality_missing_data():
    c_id = create_sample_client()
    create_sample_kpi_and_result(c_id, value=None, status="NOT_AVAILABLE")

    db = TestingSessionLocal()
    insights = run_rc506_analysis(db, c_id, "2026-08")
    db.close()

    dq_insight = next(i for i in insights if i.analysis_type == "DATA_QUALITY")
    assert dq_insight.severity == "NOT_AVAILABLE"


# ── TEST 11: No Fake Causality ────────────────────────────────────────
def test_11_no_fake_causality():
    c_id = create_sample_client()
    create_sample_kpi_and_result(c_id, value=84.02, target=90.0, status="BELOW_TARGET")

    db = TestingSessionLocal()
    insights = run_rc506_analysis(db, c_id, "2026-08")
    db.close()

    for ins in insights:
        # Verificar que el texto sea empírico y no contenga hipótesis de causa no probadas
        assert "porque faltaron operadores" not in ins.description
        assert "culpa del equipo" not in ins.description


# ── TEST 12: List Analysis Rules ─────────────────────────────────────
def test_12_list_analysis_rules():
    res = client.get("/api/admin/analysis/rules", headers=get_admin_headers())
    assert res.status_code == 200
    rules = res.json()
    assert len(rules) >= 6
    assert any(r["rule_id"] == "rule_target_compliance_v1" for r in rules)


# ── TEST 13: Run Analysis Endpoint ───────────────────────────────────
def test_13_run_analysis_endpoint():
    c_id = create_sample_client()
    create_sample_kpi_and_result(c_id, period="2026-08")

    res = client.post(f"/api/admin/analysis/run?client_id={c_id}&period=2026-08", headers=get_admin_headers())
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1


# ── TEST 14: Get Client Insights Filter ──────────────────────────────
def test_14_get_client_insights_filter():
    c_id = create_sample_client()
    create_sample_kpi_and_result(c_id, value=80.0, target=90.0, status="BELOW_TARGET")
    client.post(f"/api/admin/analysis/run?client_id={c_id}&period=2026-08", headers=get_admin_headers())

    res = client.get(f"/api/admin/analysis/clients/{c_id}/insights?period=2026-08&analysis_type=TARGET_COMPLIANCE", headers=get_admin_headers())
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["analysis_type"] == "TARGET_COMPLIANCE"


# ── TEST 15: Insight Traceability Endpoint ───────────────────────────
def test_15_insight_traceability_endpoint():
    c_id = create_sample_client()
    create_sample_kpi_and_result(c_id, period="2026-08")
    res_run = client.post(f"/api/admin/analysis/run?client_id={c_id}&period=2026-08", headers=get_admin_headers())
    ins_id = res_run.json()[0]["id"]

    res_trace = client.get(f"/api/admin/analysis/insights/{ins_id}/traceability", headers=get_admin_headers())
    assert res_trace.status_code == 200
    data = res_trace.json()
    assert data["insight_id"] == ins_id
    assert "kpi_info" in data
    assert "raw_import_info" in data


# ── TEST 16: Security Authorization ─────────────────────────────────
def test_16_security_authorization():
    res1 = client.post("/api/admin/analysis/run?client_id=1&period=2026-08")
    assert res1.status_code == 401

    res2 = client.get("/api/admin/analysis/clients/1/insights")
    assert res2.status_code == 401


# ── TEST 17: Regression Fases 01 to 04 ────────────────────────────────
def test_17_regression_fases01_to_04():
    # Fase 01
    assert client.get("/api/admin/dashboard-global", headers=get_admin_headers()).status_code == 200
    # Fase 02
    assert client.get("/api/admin/imports/", headers=get_admin_headers()).status_code == 200
    # Fase 04
    assert client.get("/api/admin/kpis/results", headers=get_admin_headers()).status_code == 200
