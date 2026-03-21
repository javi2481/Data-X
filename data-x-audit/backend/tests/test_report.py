import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def test_get_report(client, auth_headers):
    # Crear una sesión primero
    file_path = FIXTURES_DIR / "ventas.csv"
    with open(file_path, "rb") as f:
        files = {"file": ("ventas.csv", f, "text/csv")}
        res = client.post("/api/sessions", files=files, headers=auth_headers)
    
    session_id = res.json()["session_id"]
    
    # Obtener el reporte
    response = client.get(f"/api/sessions/{session_id}/report", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "findings" in data
    if len(data["findings"]) > 0:
        first = data["findings"][0]
        assert "what" in first
        assert "so_what" in first
        assert "now_what" in first
        assert first["severity"] in ["critical", "important", "suggestion", "insight"]
    assert "chart_specs" in data
    assert "data_preview" in data
    assert "dataset_overview" in data
    assert "column_profiles" in data
    assert "schema_version" in data["provenance"]
    assert "provenance_refs" in data["provenance"]
    assert "document_context" in data
    assert "document_tables" in data
    assert "document_metadata" in data
    assert "selected_table_index" in data

def test_report_not_found(client, auth_headers):
    response = client.get("/api/sessions/no_existe/report", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["error_code"] == "SESSION_NOT_FOUND"
