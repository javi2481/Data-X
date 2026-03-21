from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.client import db
import json
import asyncio

async def test_data_preview():
    print("--- Test: data_preview en Report ---")
    
    # Inicializar DB para el test
    await db.connect_to_db()
    
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. Crear sesión
            file_path = "tests/fixtures/ventas.csv"
            with open(file_path, "rb") as f:
                response = await ac.post("/api/sessions", files={"file": ("ventas.csv", f, "text/csv")})
            
            if response.status_code != 200:
                print(f"Error creando sesión: {response.status_code}")
                print(response.json())
                return

            session_id = response.json()["session_id"]
            print(f"Sesión creada: {session_id}")

            # 2. Obtener reporte
            response = await ac.get(f"/api/sessions/{session_id}/report")
            if response.status_code != 200:
                print(f"Error obteniendo reporte: {response.status_code}")
                print(response.json())
                return

            report = response.json()
            
            if "data_preview" in report:
                preview = report["data_preview"]
                print(f"data_preview encontrado: {len(preview)} filas")
                if len(preview) > 0:
                    print("Muestra de la primera fila:")
                    print(json.dumps(preview[0], indent=2))
                    print("SUCCESS: data_preview restaurado correctamente")
                else:
                    print("FAIL: data_preview está vacío")
            else:
                print("FAIL: data_preview no encontrado en el reporte")
            
    finally:
        await db.close_db_connection()

if __name__ == "__main__":
    asyncio.run(test_data_preview())
