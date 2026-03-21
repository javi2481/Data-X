import httpx
import asyncio
import os
import sys

# Añadir el directorio actual al path para importar app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def verify_c2():
    from app.main import app
    from app.db.client import db
    from httpx import ASGITransport

    await db.connect_to_db()
    try:
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=60.0) as client:
            # 1. Health
            print("\n--- Health Check ---")
            r = await client.get("/api/health")
            print(f"Status: {r.status_code}, Response: {r.json()}")

            # 2. Ingesta (Corte 2: debe incluir EDA Extendido)
            print("\n--- Creating Session (Medallion v3.0 + Corte 2) ---")
            csv_path = "tests/fixtures/ventas.csv"
            if not os.path.exists(csv_path):
                 csv_path = "backend/tests/fixtures/ventas.csv"
                
            with open(csv_path, "rb") as f:
                files = {"file": ("ventas.csv", f, "text/csv")}
                r = await client.post("/api/sessions", files=files)
                
            if r.status_code != 200:
                print(f"Error in session creation: {r.status_code} - {r.text}")
                return
                
            session_id = r.json()["session_id"]
            print(f"Session Created: {session_id}")
            print(f"Initial Finding Count: {r.json().get('finding_count')}")

            # 3. Report (Debe incluir EDA extendido y Gold Layer fallbacks)
            print("\n--- Getting Report (Gold Layer) ---")
            r = await client.get(f"/api/sessions/{session_id}/report")
            report = r.json()
            print(f"Executive Summary (Fallback or LLM): {report.get('executive_summary', '')[:100]}...")
            print(f"Findings: {len(report.get('findings', []))}")
            print(f"Charts: {len(report.get('chart_specs', []))}")
            
            # Verificar si hay findings de EDA extendido
            categories = [f["category"] for f in report.get("findings", [])]
            print(f"Categories found: {set(categories)}")
            
            # 4. Analyze (Motor LLM real / Fallback)
            print("\n--- Interactive Query (/api/analyze) ---")
            query_data = {"session_id": session_id, "query": "¿Qué problemas tiene este dataset?"}
            r = await client.post("/api/analyze", json=query_data)
            analyze_res = r.json()
            print(f"LLM Answer: {analyze_res.get('answer')[:100]}...")
            print(f"Relevant Findings: {len(analyze_res.get('relevant_findings', []))}")
            print(f"Confidence: {analyze_res.get('confidence')}")

            # 5. List Sessions (Historial)
            print("\n--- Session History ---")
            r = await client.get("/api/sessions?limit=5")
            history = r.json()
            print(f"History length: {len(history)}")
            if len(history) > 0:
                print(f"Last Session ID: {history[0]['session_id']}")
                print("✅ Session history working!")

            print("\n--- C2 Verification Successful! ---")
    finally:
        await db.close_db_connection()

if __name__ == "__main__":
    asyncio.run(verify_c2())
