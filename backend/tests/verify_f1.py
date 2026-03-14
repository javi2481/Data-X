import sys
import os
from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_f1():
    print("=== Iniciando Verificación F1 ===")
    
    # 1. Health check
    print("\n1. Health check: /api/health")
    response = client.get("/api/health")
    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")
    assert response.status_code == 200
    
    # 2. Crear sesión con CSV
    print("\n2. Crear sesión: POST /api/sessions")
    fixture_path = "tests/fixtures/ventas.csv"
    if not os.path.exists(fixture_path):
        print(f"ERROR: No se encuentra {fixture_path}")
        return
        
    with open(fixture_path, "rb") as f:
        files = {"file": ("ventas.csv", f, "text/csv")}
        response = client.post("/api/sessions", files=files)
    
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Body error: {response.text}")
        return
        
    data = response.json()
    session_id = data.get("session_id")
    print(f"Session ID: {session_id}")
    assert session_id is not None
    
    # 3. Obtener estado de sesión
    print(f"\n3. Estado de sesión: /api/sessions/{session_id}")
    response = client.get(f"/api/sessions/{session_id}")
    print(f"Status: {response.status_code}")
    print(f"Body: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    
    # 4. Obtener reporte completo
    print(f"\n4. Reporte completo: /api/sessions/{session_id}/report")
    response = client.get(f"/api/sessions/{session_id}/report")
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Body error: {response.text}")
    else:
        report = response.json()
        print(f"Findings: {len(report.get('findings', []))}")
        print(f"Chart Specs: {len(report.get('chart_specs', []))}")
    assert response.status_code == 200
    
    # 5. Probar /api/analyze
    print(f"\n5. Análisis: POST /api/analyze")
    analyze_payload = {"session_id": session_id, "query": "Analiza los datos"}
    response = client.post("/api/analyze", json=analyze_payload)
    print(f"Status: {response.status_code}")
    print(f"Body summary: {response.json().get('summary')}")
    assert response.status_code == 200
    
    print("\n=== Verificación F1 COMPLETADA con ÉXITO ===")

if __name__ == "__main__":
    try:
        with TestClient(app) as c:
            # Reasignamos client para usar el context manager que arranca el lifespan
            client = c
            test_f1()
    except Exception as e:
        print(f"\n!!! ERROR DURANTE LA VERIFICACIÓN !!!")
        print(str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
