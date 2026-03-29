# Data-X

[![CI Pipeline](https://github.com/javi2481/data-x/actions/workflows/ci.yml/badge.svg)](https://github.com/javi2481/data-x/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/next.js-15-black)](https://nextjs.org/)

**Plataforma inteligente para el análisis de documentos y datos estructurados.**

Data-X implementa una arquitectura Medallion (Bronze → Silver → Gold) para el procesamiento determinístico de datos con enriquecimiento por IA, siguiendo un enfoque "Docling-first" para el manejo de documentos.

## Tech Stack

| Capa | Tecnología |
|------|------------|
| **Backend** | FastAPI, Python 3.11+, Pydantic v2 |
| **Frontend** | Next.js 14, React, TypeScript, Tailwind CSS, shadcn/ui |
| **Base de Datos** | MongoDB (PyMongo Async) |
| **Procesamiento** | Docling, HybridChunker, Pandas, Pandera |
| **IA/LLM** | LiteLLM (OpenRouter, OpenAI, etc.) |
| **Embeddings** | FAISS, sentence-transformers |
| **Package Manager** | uv (recomendado) o pip |

## Características Principales

- **Pipeline Medallion**: Procesamiento en capas (Bronze: raw, Silver: profiling/findings, Gold: enrichment)
- **Docling-first**: Extracción inteligente de documentos con provenance completo
- **Finding-Centric**: Detección automática de hallazgos (nulos, duplicados, outliers, patrones)
- **RAG Integrado**: Consultas semánticas sobre documentos procesados
- **Preguntas Sugeridas**: Generación contextual de preguntas relevantes

## Quick Start

### Backend

```bash
cd backend

# Con uv (recomendado)
./scripts.sh install
./scripts.sh server

# Con pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
yarn install
yarn dev
```

### Variables de Entorno

**Backend** (`backend/.env`):
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=datax
LITELLM_API_KEY=sk-...
LITELLM_MODEL=openrouter/openai/gpt-4o-mini
JWT_SECRET_KEY=your-secret-key
```

**Frontend** (`frontend/.env`):
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## Estructura del Proyecto

```
data-x/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/routes/    # Endpoints
│   │   ├── schemas/       # Pydantic models
│   │   ├── services/      # Business logic
│   │   ├── repositories/  # Data access
│   │   └── db/            # Database client
│   ├── tests/             # pytest tests
│   ├── pyproject.toml     # uv/pip config
│   └── scripts.sh         # Dev scripts
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── app/           # Pages (App Router)
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities
│   │   └── types/         # TypeScript types
│   └── package.json
├── docs/                  # Documentation
├── memory/                # PRD and planning
├── AGENTS.md              # Agent guidelines
└── docker-compose.yml     # Docker setup
```

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/sessions` | Upload y análisis de archivo |
| GET | `/api/sessions/{id}/report` | Reporte completo |
| POST | `/api/analyze` | Query RAG interactivo |
| GET | `/api/analyze/{id}/suggested-questions` | Preguntas sugeridas |

## Documentación Adicional

- [AGENTS.md](./AGENTS.md) - Guía para agentes de desarrollo
- [docs/UV_MIGRATION_ANALYSIS.md](./docs/UV_MIGRATION_ANALYSIS.md) - Análisis de migración a uv
- [memory/PRD.md](./memory/PRD.md) - Product Requirements Document

## Licencia

MIT
