import pytest
import os
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def test_create_session_csv(client, auth_headers):
    file_path = FIXTURES_DIR / "ventas.csv"
    with open(file_path, "rb") as f:
        files = {"file": ("ventas.csv", f, "text/csv")}
        response = client.post("/api/sessions", files=files, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["status"] in ["ready", "processing", "created"]

def test_create_session_invalid_file(client, auth_headers):
    # Crear un archivo temporal .txt
    with open("test.txt", "w") as f:
        f.write("esto no es un csv")
    
    with open("test.txt", "rb") as f:
        files = {"file": ("test.txt", f, "text/plain")}
        response = client.post("/api/sessions", files=files, headers=auth_headers)
    
    os.remove("test.txt")
    assert response.status_code == 400
    assert response.json()["error_code"] == "UNSUPPORTED_FORMAT"

def test_create_session_empty_file(client, auth_headers):
    # Crear un archivo vacío
    with open("empty.csv", "wb") as f:
        pass
    
    with open("empty.csv", "rb") as f:
        files = {"file": ("empty.csv", f, "text/csv")}
        response = client.post("/api/sessions", files=files, headers=auth_headers)
    
    os.remove("empty.csv")
    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_FILE"

def test_get_session(client, auth_headers):
    # Primero crear una
    file_path = FIXTURES_DIR / "ventas.csv"
    with open(file_path, "rb") as f:
        files = {"file": ("ventas.csv", f, "text/csv")}
        res = client.post("/api/sessions", files=files, headers=auth_headers)
    
    session_id = res.json()["session_id"]
    
    # Luego obtenerla
    response = client.get(f"/api/sessions/{session_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["session_id"] == session_id

def test_get_session_not_found(client, auth_headers):
    response = client.get("/api/sessions/session_no_existe", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["error_code"] == "SESSION_NOT_FOUND"
