# Data-X Backend API (Arquitectura v3.0 Medallion)

Backend oficial de Data-X, una plataforma inteligente para el análisis y visualización de datos estructurados. Implementa una arquitectura Medallion (Bronze/Silver/Gold) para el procesamiento determinístico y enriquecimiento por IA.

## Características principales (Corte 3)

- **Arquitectura Medallion**: Flujo de datos organizado en capas (Bronze: Raw, Silver: Profiling/Schema/Findings, Gold: Executive Summary/IA).
- **Finding-Centric**: El análisis se basa en "Hallazgos" (Findings) detectados automáticamente.
- **ChartSpecs Agnósticos**: Generación de especificaciones de gráficos listas para ser renderizadas por cualquier librería.
- **Ingesta Multiformato (Docling)**: Pipeline unificado para procesar CSV, XLSX y PDF con extracción inteligente de tablas.
- **Schema Validation (Pandera)**: Validación automática de la estructura de datos en el pipeline Silver.
- **Enriquecimiento con IA (Gold)**: Resúmenes ejecutivos y explicaciones inteligentes vía LiteLLM con retry y fallback determinístico.
- **Observabilidad**: Instrumentación nativa con OpenTelemetry e índices optimizados en MongoDB.
- **Tests Formales**: Suite de pruebas con pytest para garantizar la integridad del sistema.

## Requisitos previos

- Python 3.11+
- MongoDB (instancia local o Atlas)

## Instalación

1. Crear un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: .\venv\Scripts\activate
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Configurar variables de entorno (.env):
   ```env
   MONGODB_URI=mongodb://...
   MONGODB_DB=datax
   LITELLM_API_KEY=sk-...
   LITELLM_MODEL=gpt-4o-mini
   CORS_ORIGINS=["http://localhost:3000"]
   ```

## Ejecución

```bash
uvicorn app.main:app --reload --port 8000
```

## Pruebas (Tests)

```bash
$env:PYTHONPATH = "." # En PowerShell
python -m pytest tests/ -v
```

El servidor estará disponible en `http://localhost:8000`.
La documentación Swagger UI en `http://localhost:8000/docs`.

## Endpoints Principales

### 1. Health Check
`GET /api/health`
```bash
curl http://localhost:8000/api/health
```

### 2. Crear Sesión (Bronze -> Silver -> Gold)
`POST /api/sessions` - Sube un CSV, XLSX o PDF, ejecuta el perfilado, valida esquema y genera hallazgos e interpretación.
```bash
curl -X POST http://localhost:8000/api/sessions -F "file=@ruta/archivo.xlsx"
```

### 3. Obtener Reporte Completo
`GET /api/sessions/{id}/report` - Devuelve el AnalysisReport con findings y charts.
```bash
curl http://localhost:8000/api/sessions/TU_SESSION_ID/report
```

### 4. Análisis (Compatibilidad)
`POST /api/analyze` - Consulta interactiva sobre la sesión.
```bash
curl -X POST http://localhost:8000/api/analyze \
     -H "Content-Type: application/json" \
     -d '{"session_id": "TU_ID", "query": "Analiza esto"}'
```

## Servicios del Backend (Corte 3)

- **IngestService**: Pipeline Docling para CSV, XLSX y PDF con fallback determinístico.
- **FindingBuilder**: Corazón del análisis. Detecta nulos, duplicados, correlaciones, outliers, distribuciones y problemas de esquema.
- **SchemaValidator (Pandera)**: Infiere y valida el esquema del dataset automáticamente.
- **LLMService (Gold)**: Capa de IA con LiteLLM. Genera resúmenes ejecutivos y explicaciones enriquecidas con mecanismo de retry.
- **ChartSpecGenerator**: Transforma hallazgos y datos en especificaciones visuales (scatter plots, histogramas, heatmaps).
- **NormalizationService**: Limpia headers (unicodedata) y coerciona tipos.
- **ProfilerService**: Perfilado estadístico profundo por columna (NaN-safe).
- **EDAExtendedService**: Análisis estadístico avanzado (correlaciones de Pearson, outliers IQR/Z-score, distribuciones).

## Roadmap
- **Corte 4**: Mejoras en UI y exportación de reportes.
- **Corte 5**: Integración de bases de datos relacionales.
