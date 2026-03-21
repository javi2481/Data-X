# Data-X

[![CI](https://github.com/javi2481/data-x/actions/workflows/ci.yml/badge.svg)](https://github.com/javi2481/data-x/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Tus datos tienen respuestas. Data-X te las encuentra.

Subí cualquier archivo — Excel, CSV o PDF — y obtené un análisis completo en menos de un minuto. Data-X te dice qué encontró, por qué importa y qué hacer. Sin código. Sin estadística.

- ✓ Lee PDFs con tablas como lo haría un analista — incluso los escaneados
- ✓ Cada hallazgo está calculado, no inventado por la IA
- ✓ Preguntale cualquier cosa a tus datos en español y obtené respuestas con evidencia

---

## Estructura del proyecto

```
data-x/
├── backend/    # Python / FastAPI / MongoDB / Docling
├── frontend/   # Next.js / React / TypeScript
├── docs/       # Documentación y planes de producto
└── datasets/   # Datos de ejemplo
```

## Inicio rápido

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Accedé a `http://localhost:3000`.

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [AGENTS.md](./AGENTS.md) | Contexto completo para agentes (Emergent, v0, Junie, Claude Code) |
| [docs/product-focus.md](./docs/product-focus.md) | Visión de producto, usuarios, copy, monetización |
| [docs/roadmap-2026.md](./docs/roadmap-2026.md) | Roadmap MVP → V1 → V2 desde la perspectiva del usuario |
| [docs/implementation-plan-corte6.md](./docs/implementation-plan-corte6.md) | 25 prompts atómicos para el Corte 6 |
| [docs/claude-code-strategic-audit.md](./docs/claude-code-strategic-audit.md) | Auditoría técnica y estratégica completa |
| [docs/deploy-guide.md](./docs/deploy-guide.md) | Guía de despliegue en producción |
