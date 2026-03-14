# Data-X Backend API

Backend oficial de Data-X, una plataforma inteligente para el análisis y visualización de datos estructurados. Construido con Python, FastAPI, MongoDB y LiteLLM.

## Características principales

- **Ingesta Docling-First**: Pipeline unificado para procesar archivos (CSV inicialmente) con extracción inteligente de tablas.
- **Análisis Estadístico**: Perfilado detallado por columna y motor de estadísticas descriptivas.
- **Inteligencia Artificial**: Resúmenes y respuestas generadas con LLMs mediante LiteLLM.
- **Visualización**: Generación de configuraciones de gráficos compatibles con Recharts.
- **Observabilidad**: Instrumentación nativa con OpenTelemetry y logs estructurados.

## Requisitos previos

- Python 3.10+
- MongoDB (instancia local o Atlas)
- Clave de API para proveedores de LLM (OpenAI, Anthropic, etc.) si se desea usar LiteLLM completo.

## Instalación

1. Crear un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   # Editar .env con tus credenciales de MongoDB y API Keys
   ```

## Ejecución

```bash
uvicorn app.main:app --reload --port 8000
```

El servidor estará disponible en `http://localhost:8000`.
La documentación Swagger UI en `http://localhost:8000/docs`.

## Endpoints Principales

### 1. Health Check
`GET /health`
```bash
curl http://localhost:8000/health
```

### 2. Crear Sesión (Upload)
`POST /sessions` - Sube un CSV y crea una sesión de análisis.
```bash
curl -X POST http://localhost:8000/sessions -F "file=@ruta/a/tu/archivo.csv"
```

### 3. Analizar Sesión
`POST /analyze` - Ejecuta una consulta sobre los datos de la sesión.
```bash
curl -X POST http://localhost:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{"session_id": "TU_SESSION_ID", "query": "Dame un resumen de los datos"}'
```

## Servicios del Backend

- **IngestService**: Procesa archivos usando Docling o Pandas como fallback.
- **NormalizationService**: Limpia y estandariza nombres de columnas y tipos de datos.
- **ValidationService**: Detecta problemas de calidad en el dataset.
- **ProfilerService**: Genera estadísticas detalladas por cada columna.
- **StatsEngine**: Calcula correlaciones, outliers y métricas avanzadas.
- **LLMService**: Genera interpretaciones narrativas usando LiteLLM.
- **ArtifactBuilder**: Construye la respuesta visual (tablas, gráficos, métricas).
- **ProvenanceService**: Rastrea el historial de cambios en cada sesión.
