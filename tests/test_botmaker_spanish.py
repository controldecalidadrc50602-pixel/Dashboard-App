import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database import Base, get_db
from app.main import app
from app.models import Client, ReportImport, NormalizedRecord
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
    db = TestingSessionLocal()
    c = Client(name="Cliente Botmaker Test", is_active=True)
    db.add(c)
    db.commit()
    db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

def get_admin_headers():
    token = create_access_token({"sub": "admin", "role": "superadmin"})
    return {"Authorization": f"Bearer {token}"}


def test_01_users_spanish_columns_valid_and_metrics():
    # ARCHIVO 1 — users-*.tsv (Conversaciones)
    tsv_content = (
        "Link Conversación\tFecha Sesión\tHora Sesión\tId Sesión\tId canal\tId Contacto/Número\tHabló el Agente\tMensajes Usuario\tMensajes Bot\tMensajes Agente\tTipificación\n"
        "https://bm.com/c1\t2026-09-01\t10:00\tses_01\tWhatsApp\t+50688880001\t1\t5\t2\t4\tConsulta Producto\n"
        "https://bm.com/c2\t2026-09-01\t10:15\tses_02\tWhatsApp\t+50688880002\t0\t2\t3\t0\tPregunta Frecuente\n"
        "https://bm.com/c3\t2026-09-01\t10:30\tses_03\tWhatsApp\t+50688880003\t1\t8\t1\t7\tSoporte Técnico\n"
    ).encode("utf-8")

    res = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": 1, "source_code": "botmaker", "period": "2026-09"},
        files={"file": ("users-2026-09.tsv", tsv_content, "text/tab-separated-values")}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "VALID"
    assert data["report_type"] == "users"
    import_id = data["id"]

    # Procesar y normalizar
    res_proc = client.post(f"/api/admin/imports/{import_id}/process", headers=get_admin_headers())
    assert res_proc.status_code == 200
    proc_data = res_proc.json()
    metrics = res_proc.json()["calculated_metrics"]

    assert metrics["total_conversations"] == 3
    assert metrics["conversations_with_agent"] == 2
    assert metrics["conversations_bot_only"] == 1
    assert metrics["total_messages_user"] == 15
    assert metrics["total_messages_bot"] == 6
    assert metrics["total_messages_agent"] == 11


def test_02_session_starting_causes_spanish_columns_valid_and_metrics():
    # ARCHIVO 2 — sessionStartingCauses-*.tsv (Plantillas/Notificaciones)
    tsv_content = (
        "Id Usuario\tId Contacto/Número\tFecha/tiempo Inicio Sesión\tId canal\tUsuario Nuevo\tNombre Plantilla/Notificación\tNo Enviado\tEnviado\tEntregado\tLeída\tRespondida\tRazón Falla Envío\tDetalle Falla Envío\tFecha/tiempo Envío\tFecha/tiempo Entrega\tFecha/hora de lectura\tFecha/tiempo Respuesta\tGrupos Agente\n"
        "usr_1\t+50688881111\t2026-09-01 09:00:00\tWhatsApp\ttrue\tRecordatorio Cita\tfalse\ttrue\ttrue\ttrue\ttrue\t\t\t2026-09-01 09:00:00\t2026-09-01 09:00:05\t2026-09-01 09:01:00\t2026-09-01 09:02:00\tGrupo A\n"
        "usr_2\t+50688882222\t2026-09-01 09:05:00\tWhatsApp\tfalse\tPromoción Especial\tfalse\ttrue\ttrue\ttrue\tfalse\t\t\t2026-09-01 09:05:00\t2026-09-01 09:05:05\t2026-09-01 09:10:00\t\tGrupo A\n"
        "usr_3\t+50688883333\t2026-09-01 09:10:00\tWhatsApp\ttrue\tAlerta Seguridad\ttrue\tfalse\tfalse\tfalse\tfalse\tError de red\tTimeout\t2026-09-01 09:10:00\t\t\t\tGrupo B\n"
    ).encode("utf-8")

    res = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": 1, "source_code": "botmaker", "period": "2026-09"},
        files={"file": ("sessionStartingCauses-2026-09.tsv", tsv_content, "text/tab-separated-values")}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "VALID"
    assert data["report_type"] in ["session_causes", "sessionStartingCauses"]
    import_id = data["id"]

    res_proc = client.post(f"/api/admin/imports/{import_id}/process", headers=get_admin_headers())
    assert res_proc.status_code == 200
    metrics = res_proc.json()["calculated_metrics"]

    assert metrics["total_templates_sent"] == 2
    assert metrics["total_templates_delivered"] == 2
    assert metrics["total_templates_read"] == 2
    assert metrics["total_templates_responded"] == 1
    assert metrics["total_templates_failed"] == 1
    assert metrics["new_users"] == 2


def test_03_operators_sessions_debug_spanish_columns_with_description_row():
    # ARCHIVO 3 — operatorsSessionsDebug-*.tsv (Sesiones de Agentes con fila 2 de descripciones)
    tsv_content = (
        "Id Sesión\tId Usuario\tFecha/tiempo Inicio Sesión\tNombre Agente\tId Agente\tCola\tTipificación\tFecha/tiempo Cierre\tConversaciones en curso\tConversaciones cerradas\tPospuestas\tTiempo medio de respuesta\tCantidad de respuestas\tTransferencias recibidas\tTransferencias realizadas\tLink Conversación\n"
        "Identificador único de la sesión\tIdentificador del usuario\tFecha y hora en que inició\tNombre del agente asignado\tId del agente\tCola de atención\tTipificación de la sesión\tFecha y hora de cierre\tConversaciones activas\tConversaciones finalizadas\tPospuestas\tTiempo promedio de espera\tRespuestas\tRecibidas\tRealizadas\tLink a la conversación\n"
        "ses_001\tusr_101\t2026-09-01 10:00:00\tLaura Gomez\tagt_10\tVentas\tVenta Exitosa\t2026-09-01 10:15:00\t0\t5\t0\t00:01:30\t10\t2\t1\thttps://bm.com/c1\n"
        "ses_002\tusr_102\t2026-09-01 11:00:00\tCarlos Perez\tagt_20\tSoporte\tConsulta\t2026-09-01 11:20:00\t1\t3\t1\t45s\t6\t0\t0\thttps://bm.com/c2\n"
    ).encode("utf-8")

    res = client.post(
        "/api/admin/imports/",
        headers=get_admin_headers(),
        data={"client_id": 1, "source_code": "botmaker", "period": "2026-09"},
        files={"file": ("operatorsSessionsDebug-2026-09.tsv", tsv_content, "text/tab-separated-values")}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "VALID"
    assert data["report_type"] in ["operators_debug", "operatorsSessionsDebug"]
    import_id = data["id"]

    # Vista previa RAW debe excluir la fila 2 de descripciones y mostrar filas de datos
    res_prev = client.get(f"/api/admin/imports/{import_id}/preview", headers=get_admin_headers())
    assert res_prev.status_code == 200
    prev_data = res_prev.json()
    assert prev_data["sample_rows"][0][0] == "ses_001"
    assert prev_data["total_rows"] == 2

    res_proc = client.post(f"/api/admin/imports/{import_id}/process", headers=get_admin_headers())
    assert res_proc.status_code == 200
    metrics = res_proc.json()["calculated_metrics"]

    assert metrics["total_agent_sessions"] == 2
    assert metrics["total_closed_conversations"] == 8
    # 00:01:30 = 90s, 45s = 45s -> avg = 67.5s
    assert metrics["avg_response_time"] == 67.5
    assert metrics["total_transfers_received"] == 2
    assert metrics["agents_list"] == ["Carlos Perez", "Laura Gomez"]
    assert metrics["typifications"] == {"Venta Exitosa": 1, "Consulta": 1}


def test_04_full_ingestion_flow_sync_monthly_report_and_kpis():
    # Flujo completo: Subida -> Detección -> Normalización -> Sync MonthlyReport -> Evaluación KPIs
    tsv_users = (
        "Link Conversación\tFecha Sesión\tHora Sesión\tId Sesión\tId canal\tId Contacto/Número\tHabló el Agente\tMensajes Usuario\tMensajes Bot\tMensajes Agente\tTipificación\n"
        "https://bm.com/c1\t2026-09-01\t10:00\tses_01\tWhatsApp\t+50688880001\t1\t5\t2\t4\tConsulta Producto\n"
        "https://bm.com/c2\t2026-09-01\t10:15\tses_02\tWhatsApp\t+50688880002\t0\t2\t3\t0\tPregunta Frecuente\n"
    ).encode("utf-8")

    tsv_causes = (
        "Id Usuario\tId Contacto/Número\tFecha/tiempo Inicio Sesión\tId canal\tUsuario Nuevo\tNombre Plantilla/Notificación\tNo Enviado\tEnviado\tEntregado\tLeída\tRespondida\tRazón Falla Envío\tDetalle Falla Envío\tFecha/tiempo Envío\tFecha/tiempo Entrega\tFecha/hora de lectura\tFecha/tiempo Respuesta\tGrupos Agente\n"
        "usr_1\t+50688881111\t2026-09-01 09:00:00\tWhatsApp\ttrue\tRecordatorio Cita\tfalse\ttrue\ttrue\ttrue\ttrue\t\t\t2026-09-01 09:00:00\t2026-09-01 09:00:05\t2026-09-01 09:01:00\t2026-09-01 09:02:00\tGrupo A\n"
    ).encode("utf-8")

    tsv_operators = (
        "Id Sesión\tId Usuario\tFecha/tiempo Inicio Sesión\tNombre Agente\tId Agente\tCola\tTipificación\tFecha/tiempo Cierre\tConversaciones en curso\tConversaciones cerradas\tPospuestas\tTiempo medio de respuesta\tCantidad de respuestas\tTransferencias recibidas\tTransferencias realizadas\tLink Conversación\n"
        "Identificador único de la sesión\tIdentificador del usuario\tFecha y hora en que inició\tNombre del agente asignado\tId del agente\tCola de atención\tTipificación de la sesión\tFecha y hora de cierre\tConversaciones activas\tConversaciones finalizadas\tPospuestas\tTiempo promedio de espera\tRespuestas\tRecibidas\tRealizadas\tLink a la conversación\n"
        "ses_001\tusr_101\t2026-09-01 10:00:00\tLaura Gomez\tagt_10\tVentas\tVenta Exitosa\t2026-09-01 10:15:00\t0\t5\t0\t00:01:30\t10\t2\t1\thttps://bm.com/c1\n"
    ).encode("utf-8")

    headers = get_admin_headers()

    # 1. Subida
    res_u = client.post("/api/admin/imports/", headers=headers, data={"client_id": 1, "source_code": "botmaker", "period": "2026-09"}, files={"file": ("users-2026-09.tsv", tsv_users, "text/tab-separated-values")})
    res_c = client.post("/api/admin/imports/", headers=headers, data={"client_id": 1, "source_code": "botmaker", "period": "2026-09"}, files={"file": ("sessionStartingCauses-2026-09.tsv", tsv_causes, "text/tab-separated-values")})
    res_o = client.post("/api/admin/imports/", headers=headers, data={"client_id": 1, "source_code": "botmaker", "period": "2026-09"}, files={"file": ("operatorsSessionsDebug-2026-09.tsv", tsv_operators, "text/tab-separated-values")})

    assert res_u.json()["status"] == "VALID"
    assert res_c.json()["status"] == "VALID"
    assert res_o.json()["status"] == "VALID"

    # 2. Procesamiento
    client.post(f"/api/admin/imports/{res_u.json()['id']}/process", headers=headers)
    client.post(f"/api/admin/imports/{res_c.json()['id']}/process", headers=headers)
    client.post(f"/api/admin/imports/{res_o.json()['id']}/process", headers=headers)

    # 3. Verificar que MonthlyReport fue creado en BD y expone métricas en Dashboard Individual
    res_reports = client.get("/api/clients/1/reports?year=2026", headers=headers)
    assert res_reports.status_code == 200
    reports = res_reports.json()
    rep_sep = next((r for r in reports if r["month"] == 9), None)
    assert rep_sep is not None
    assert rep_sep["chats"] > 0

    bm = rep_sep["extra_data"]["botmaker"]
    assert bm["total_conversations"] == 2
    assert bm["total_templates_sent"] == 1
    assert bm["total_agent_sessions"] == 1
    assert bm["agents_list"] == ["Laura Gomez"]

    # 4. Verificar evaluación del Motor de KPIs
    res_kpis = client.get("/api/admin/kpis/results?client_id=1&period=2026-09", headers=headers)
    assert res_kpis.status_code == 200

