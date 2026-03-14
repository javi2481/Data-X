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

# Fixture para verificar conexión a MongoDB
@pytest.fixture
async def check_mongo():
    from app.db.client import db
    try:
        # Intentar conectar si no está ya conectado
        if db.client is None:
            await db.connect_to_db()
        # Verificar si podemos hacer una operación simple
        await db.client.admin.command('ping')
        return True
    except Exception:
        return False
