# Data-X Backend API (Arquitectura v3.0 Medallion)

Backend oficial de Data-X, una plataforma inteligente para el análisis y visualización de datos estructurados. Implementa una arquitectura Medallion (Bronze/Silver/Gold) para el procesamiento determinístico y enriquecimiento por IA.

## Características principales

- **Arquitectura Medallion**: Flujo de datos organizado en capas (Bronze: Raw, Silver: Profiling/Schema/Findings, Gold: Executive Summary/IA).
- **Docling-first**: Pipeline de documentos con provenance completo (página, bbox, secciones).
- **Finding-Centric**: El análisis se basa en "Hallazgos" (Findings) detectados automáticamente.
- **HybridChunker**: Chunking semántico con límites de tokens para embeddings.
- **PyMongo Async**: Base de datos MongoDB con API asíncrona nativa (migrado de Motor).
- **ChartSpecs Agnósticos**: Generación de especificaciones de gráficos listas para ser renderizadas por cualquier librería.

## Requisitos previos

- Python 3.11+
- MongoDB (instancia local o Atlas)
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip

## Instalación

### Con uv (Recomendado - 10x más rápido)

```bash
# Instalar uv si no lo tenés
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependencias
uv sync

# O usar el script de ayuda
./scripts.sh install
```

### Con pip (Legacy)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuración

Crear archivo `.env`:
```env
MONGODB_URI=mongodb://...
MONGODB_DB=datax
LITELLM_API_KEY=sk-...
LITELLM_MODEL=gpt-4o-mini
CORS_ORIGINS=["http://localhost:3000"]
```

## Ejecución

### Con uv
```bash
./scripts.sh server
# o
uv run uvicorn app.main:app --reload --port 8001
```

### Con pip
```bash
uvicorn app.main:app --reload --port 8001
```

## Scripts de Desarrollo (uv)

```bash
./scripts.sh install      # Instalar dependencias
./scripts.sh install-dev  # Instalar deps de desarrollo
./scripts.sh test         # Ejecutar pytest
./scripts.sh lint         # Ejecutar ruff
./scripts.sh format       # Formatear código
./scripts.sh server       # Iniciar servidor
./scripts.sh upgrade      # Actualizar dependencias
./scripts.sh clean        # Limpiar caches
```

## Pruebas

```bash
# Con uv
./scripts.sh test

# Con pip
python -m pytest tests/ -v
```

## Documentación API

- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/sessions` | Crear sesión (upload archivo) |
| GET | `/api/sessions/{id}/report` | Obtener reporte completo |
| POST | `/api/analyze` | Consulta interactiva |
| GET | `/api/analyze/{id}/suggested-questions` | Preguntas sugeridas |

## Arquitectura de Servicios

- **IngestService**: Pipeline Docling para CSV, XLSX y PDF
- **DoclingChunkingService**: HybridChunker con provenance
- **FindingBuilder**: Detección de hallazgos (nulos, duplicados, outliers)
- **SuggestedQuestionsService**: Generación de preguntas contextuales
- **EmbeddingService**: Índice híbrido FAISS para búsqueda semántica
- **PerformanceOptimizer**: Batch processing y caching para documentos grandes
- **LLMService**: Enriquecimiento con IA (LiteLLM)

## Migraciones Importantes

### Sprint 3: Motor → PyMongo Async
Motor está deprecado (EOL Mayo 2026). Migramos a `AsyncMongoClient` de PyMongo nativo.

### Sprint 4: pip → uv
uv ofrece instalación 10x más rápida y lockfiles cross-platform.

## Roadmap
- Multi-document sessions
- Document comparison
- Real-time collaboration
