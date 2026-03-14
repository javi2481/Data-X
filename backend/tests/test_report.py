import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def test_get_report(client):
    # Crear una sesión primero
    file_path = FIXTURES_DIR / "ventas.csv"
    with open(file_path, "rb") as f:
        files = {"file": ("ventas.csv", f, "text/csv")}
        res = client.post("/api/sessions", files=files)
    
    session_id = res.json()["session_id"]
    
    # Obtener el reporte
    response = client.get(f"/api/sessions/{session_id}/report")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "findings" in data
    assert "chart_specs" in data
    assert "data_preview" in data
    assert "dataset_overview" in data
    assert "column_profiles" in data

def test_report_not_found(client):
    response = client.get("/api/sessions/no_existe/report")
    assert response.status_code == 404
    assert response.json()["error_code"] == "SESSION_NOT_FOUND"
