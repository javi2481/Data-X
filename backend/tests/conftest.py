import pytest
import pandas as pd
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.main import app
from pathlib import Path

# Fixture de pytest para crear FastAPI TestClient
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

# Fixture de httpx.AsyncClient para tests asíncronos
@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

# Fixture para DataFrame de prueba (desde ventas.csv)
@pytest.fixture
def ventas_df():
    path = Path(__file__).parent / "fixtures" / "ventas.csv"
    return pd.read_csv(path)

# Fixture para DataFrame con edge cases (desde edge_cases.csv)
@pytest.fixture
def edge_cases_df():
    path = Path(__file__).parent / "fixtures" / "edge_cases.csv"
    return pd.read_csv(path)

# Fixture para obtener un token de autenticación
@pytest.fixture
def auth_headers(client):
    payload = {
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    }
    # Registrarse (ignorar si ya existe)
    client.post("/api/auth/register", json=payload)
    # Loguearse
    response = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
