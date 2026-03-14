# Data-X Backend API (Arquitectura v3.0 Medallion)

Backend oficial de Data-X, una plataforma inteligente para el análisis y visualización de datos estructurados. Implementa una arquitectura Medallion (Bronze/Silver) para el procesamiento determinístico de datos antes de la interpretación.

## Características principales (Corte 1)

- **Arquitectura Medallion**: Flujo de datos organizado en capas (Bronze: Raw, Silver: Profiling/Findings).
- **Finding-Centric**: El análisis se basa en "Hallazgos" (Findings) detectados automáticamente.
- **ChartSpecs Agnósticos**: Generación de especificaciones de gráficos listas para ser renderizadas por cualquier librería (compatible con Recharts en el frontend).
- **Ingesta Docling-First**: Pipeline unificado para procesar CSVs con extracción inteligente y fallback a Pandas.
- **Observabilidad**: Instrumentación nativa con OpenTelemetry e índices optimizados en MongoDB.

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
   CORS_ORIGINS=["http://localhost:3000"]
   ```

## Ejecución

```bash
uvicorn app.main:app --reload --port 8000
```

El servidor estará disponible en `http://localhost:8000`.
La documentación Swagger UI en `http://localhost:8000/docs`.

## Endpoints Principales

### 1. Health Check
`GET /api/health`
```bash
curl http://localhost:8000/api/health
```

### 2. Crear Sesión (Bronze -> Silver)
`POST /api/sessions` - Sube un CSV, ejecuta el perfilado y detecta hallazgos.
```bash
curl -X POST http://localhost:8000/api/sessions -F "file=@ruta/archivo.csv"
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

## Servicios del Backend (Corte 1)

- **IngestService**: Pipeline dual Docling/Pandas con auto-detección de separador.
- **FindingBuilder**: Corazón del análisis. Detecta nulos, duplicados, cardinalidad y estadísticas.
- **ChartSpecGenerator**: Transforma hallazgos y datos en especificaciones visuales.
- **NormalizationService**: Limpia headers (unicodedata) y coerciona tipos.
- **ProfilerService**: Perfilado estadístico profundo por columna (NaN-safe).
- **DoclingQualityGate**: Evalúa la confianza de la extracción de datos.

## Fuera de Scope (Corte 1)
- **LiteLLM**: Desactivado (Corte 2).
- **Formatos PDF/XLSX**: Soporte limitado (Corte 2).
- **Análisis Multivariante**: (Corte 2).
