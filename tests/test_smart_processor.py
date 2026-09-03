import pytest
from app.services.smart_processor import (
    find_header_row,
    discover_schema,
    extract_metrics,
    detect_anomalies,
    process_smart_tsv
)

def test_01_find_header_row():
    raw_rows = [
        ["", "", ""],
        ["---", "---", "---"],
        ["Link Conversación", "Fecha Sesión", "Hora Sesión", "Habló el Agente", "Mensajes Usuario"],
        ["https://botmaker.com/c1", "2026-09-01", "10:00", "1", "5"],
        ["https://botmaker.com/c2", "2026-09-01", "10:05", "0", "2"]
    ]
    header_idx, headers, data_rows = find_header_row(raw_rows)
    assert header_idx == 2
    assert headers[0] == "Link Conversación"
    assert len(data_rows) == 2


def test_02_discover_schema():
    headers = ["Id Sesión", "Fecha", "Habló el Agente", "Mensajes Usuario", "Tipificación"]
    rows = [
        ["1001", "2026-09-01", "1", "12", "Soporte"],
        ["1002", "2026-09-01", "0", "3", "Ventas"],
        ["1003", "2026-09-02", "1", "8", "Soporte"],
        ["1004", "2026-09-02", "1", "15", "Consultas"],
        ["1005", "2026-09-03", "0", "2", "Ventas"]
    ]
    schema = discover_schema(headers, rows)
    assert schema["Id Sesión"]["type"] in ["id", "numeric"]
    assert schema["Fecha"]["type"] == "temporal"
    assert schema["Mensajes Usuario"]["type"] == "numeric"
    assert schema["Tipificación"]["type"] == "categorical"


def test_03_extract_metrics_spanish():
    headers = ["Link Conversación", "Fecha Sesión", "Habló el Agente", "Mensajes Usuario", "Mensajes Bot", "Mensajes Agente"]
    rows = [
        ["link1", "2026-09-01", "1", "10", "2", "8"],
        ["link2", "2026-09-01", "0", "4", "4", "0"],
        ["link3", "2026-09-01", "1", "6", "1", "5"]
    ]
    schema = discover_schema(headers, rows)
    metrics = extract_metrics(headers, rows, schema)

    assert metrics["total_conversations"] == 3
    assert metrics["conversations_with_agent"] == 2
    assert metrics["conversations_bot_only"] == 1
    assert metrics["total_messages_user"] == 20
    assert metrics["total_messages_bot"] == 7
    assert metrics["total_messages_agent"] == 13


def test_04_detect_anomalies_zscore():
    headers = ["ID", "Mensajes"]
    # Generar una distribución normal con una anomalía extrema (val = 2000)
    rows = [
        ["1", "5"], ["2", "6"], ["3", "4"], ["4", "5"], ["5", "6"],
        ["6", "5"], ["7", "4"], ["8", "5"], ["9", "6"], ["10", "2000"]
    ]
    schema = discover_schema(headers, rows)
    anomalies = detect_anomalies(headers, rows, schema)

    assert len(anomalies) >= 1
    high_anom = [a for a in anomalies if a["severity"] == "high"]
    assert len(high_anom) == 1
    assert high_anom[0]["value"] == 2000.0


def test_05_process_smart_tsv_full():
    tsv_content = (
        "Link Conversación\tFecha Sesión\tHabló el Agente\tMensajes Usuario\tMensajes Bot\n"
        "http://conv1\t2026-09-01\t1\t15\t3\n"
        "http://conv2\t2026-09-01\t0\t2\t5\n"
    ).encode("utf-8")

    res = process_smart_tsv(tsv_content, "users-2026.09.01-20.31.tsv")
    assert res["status"] in ["VALID", "VALID_WITH_WARNINGS"]
    assert res["period"] == "2026-09"
    assert res["report_type"] == "users"
    assert res["metrics"]["total_conversations"] == 2
    assert res["metrics"]["conversations_with_agent"] == 1
    assert res["metrics"]["total_messages_user"] == 17
