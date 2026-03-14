# Data-X Backend

Backend del producto Data-X. Python + FastAPI + Pydantic v2.

## Setup
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Health check
```bash
curl http://localhost:8000/health
```
