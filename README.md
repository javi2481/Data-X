# Data-X Monorepo

Plataforma unificada para el análisis de datos determinístico e inteligente. Combina el poder de **Python/FastAPI** en el backend con la agilidad de **Next.js/TypeScript** en el frontend.

## Estructura del Proyecto

```text
data-x/
├── backend/    # API REST con FastAPI, MongoDB y Docling
├── frontend/   # SPA con Next.js, Recharts y Tailwind CSS
├── docs/       # Documentación oficial y PRDs del sistema
└── datasets/   # Datos de ejemplo para pruebas
```

## Flujo de Trabajo (End-to-End)

1. **Ingesta**: Subida de archivos (CSV) procesados por **Docling** con detección automática de tablas y calidad.
2. **Pipeline**: Normalización, validación de esquemas y perfilado estadístico profundo.
3. **Análisis**: Generación de resúmenes inteligentes con **LLMs** y métricas detalladas.
4. **Visualización**: Renderizado dinámico de tablas y gráficos interactivos.
5. **Trazabilidad**: Historial completo de transformaciones (Provenance).

## Guía de Inicio Rápido

### Requisitos
- Node.js 18+
- Python 3.10+
- MongoDB Atlas o Local

### 1. Levantar el Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configura tus variables
uvicorn app.main:app --reload --port 8000
```

### 2. Levantar el Frontend
```bash
cd frontend
npm install
npm run dev
```

Accede a `http://localhost:3000` para comenzar.

## Documentación Detallada
Para más detalles sobre la arquitectura y servicios, consulta:
- [Documentación del Backend](./backend/README.md)
- [Documentación del Frontend](./frontend/README.md)
- [PRD Maestro](./docs/prd-maestro.md)
