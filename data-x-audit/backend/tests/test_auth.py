import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.client import db

@pytest.fixture(autouse=True)
async def setup_db():
    """Conectar a la DB y limpiar colección de usuarios."""
    await db.connect_to_db()
    if db.db is not None:
        await db.db.users.delete_many({})
    yield
    await db.close_db_connection()

@pytest.mark.asyncio
async def test_register_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "name": "Test User"
            }
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["name"] == "Test User"
    assert "password" not in data["user"]

@pytest.mark.asyncio
async def test_register_duplicate_email():
    payload = {
        "email": "dup@example.com",
        "password": "password123",
        "name": "Test User"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/api/auth/register", json=payload)
        response = await ac.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert "email ya está registrado" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_success():
    payload = {
        "email": "login@example.com",
        "password": "password123",
        "name": "Test User"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/api/auth/register", json=payload)
        response = await ac.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "password123"
            }
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@example.com"

@pytest.mark.asyncio
async def test_login_wrong_password():
    payload = {
        "email": "wrong@example.com",
        "password": "password123",
        "name": "Test User"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/api/auth/register", json=payload)
        response = await ac.post(
            "/api/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "wrongpassword"
            }
        )
    assert response.status_code == 401
    assert "Credenciales inválidas" in response.json()["detail"]

@pytest.mark.asyncio
async def test_protected_endpoint_without_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/auth/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token():
    payload = {
        "email": "protected@example.com",
        "password": "password123",
        "name": "Test User"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg_resp = await ac.post("/api/auth/register", json=payload)
        token = reg_resp.json()["access_token"]
        
        response = await ac.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200
    assert response.json()["email"] == "protected@example.com"
