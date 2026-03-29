# PRD Frontend

## Objetivo

Evolucionar el frontend actual para que haga visible el valor Docling-first y no se limite a presentar findings de dataset.

## Estado actual

Ya existe:
- landing
- login/register
- workspace
- findings
- charts
- query panel
- export
- historial

## Gap principal

El frontend todavía comunica más “dataset analysis” que “document intelligence”.

## Objetivo UX

El usuario debe sentir que:
- el sistema entendió su documento
- encontró tablas y contexto
- puede preguntar sobre el documento
- cada hallazgo tiene evidencia

## Flujos que deben existir al final del Corte 6

### 1. Upload
El usuario ve que puede subir CSV/XLSX/PDF/DOCX.

### 2. Processing
Mensajes de progreso orientados a valor, no a jerga técnica.

### 3. Resultados
- findings claros
- evidencia visible
- tablas detectadas
- narrativa utilizable

### 4. Query
Preguntas sobre findings y documento.

### 5. Exploración
- selector de tabla
- explorer documental inicial
- provenance panel

## Componentes a crear o reforzar

- `DocumentExplorer`
- `TableSelector`
- `EvidencePanel`
- mejoras en `QueryPanel`
- mejoras en `FileUploader`
- mejoras en `Workspace`

## Regla de presentación

Primero:
- valor
- explicación
- evidencia

Después:
- detalle técnico
- estructura
- debugging

## Criterio de éxito

El frontend deja de parecer una app para CSV con soporte PDF y pasa a parecer una plataforma capaz de entender documentos reales.

---

## Estrategia de Construcción (Post-Backend)

Una vez que el backend esté 100% sólido y todas las fases estén completadas, la construcción del frontend se acelerará utilizando una plataforma **"design-to-code"** como [Lovable.dev](https://lovable.dev).

### ¿Qué es Lovable?

Lovable es una plataforma que genera componentes de React/Next.js listos para producción directamente desde un archivo de diseño de Figma. No es un simple exportador; entiende la estructura de componentes, props, variantes y estados.

### ¿Por qué este enfoque?

1.  **Velocidad Extrema:** Reduce el tiempo de desarrollo del frontend en semanas o meses. Los componentes visuales (`FindingCard`, `ChartRenderer`, `PDFDocumentViewer`) se generan automáticamente.
2.  **Fidelidad Absoluta al Diseño:** Elimina la desconexión entre el diseño de Figma y el código final. Lo que se diseña es lo que se ve.
3.  **Foco en la Lógica:** Permite que el equipo de frontend se concentre en lo que realmente aporta valor: la gestión del estado, la interacción con la API del backend y la lógica de negocio del lado del cliente, en lugar de pasar tiempo en CSS y maquetación.

### ¿Cómo nos preparamos AHORA?

Mientras se finaliza el backend, la preparación para esta estrategia es clave:

1.  **Solidificar los Contratos de la API:** La tarea más importante. Los schemas de Pydantic del backend son la "fuente de verdad". Deben estar completos y estables, ya que definirán las `props` de los componentes del frontend. La práctica de mantener `types/contracts.ts` sincronizado es fundamental.
2.  **Diseñar en Figma para Componentes:** El proceso de diseño debe ser disciplinado, utilizando Auto Layout, Variantes y una estructura de componentes reutilizables, pensando en cómo Lovable los interpretará.
3.  **Definir un Catálogo de Componentes:** Este mismo PRD debe evolucionar para listar los componentes necesarios, sus estados y los datos de la API que consumirán. Por ejemplo:
    - **Componente:** `FindingCard`
    - **Props:** `finding: Finding` (del contrato API)
    - **Variantes:** `severity: 'critical' | 'high' | 'medium'`, `isExpanded: boolean`

Este enfoque no requiere cambios en el código del backend, solo asegura que cuando llegue el momento de construir el frontend, el proceso sea lo más eficiente posible.
