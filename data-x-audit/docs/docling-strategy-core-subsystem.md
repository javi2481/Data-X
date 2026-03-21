# Docling Strategy — Core Subsystem

## Decisión estratégica

Data-X se reconvierte a una arquitectura **Docling-first**.

Eso significa que Docling deja de ser tratado como:
- parser de PDF
- helper para extraer una tabla
- paso previo antes del DataFrame

Y pasa a ser tratado como:
- subsistema documental
- fuente de estructura
- fuente de contexto
- base para provenance
- base para chunking semántico
- base para query documental

## Estado actual

Hoy Docling ya está integrado, pero su uso es parcial:
- convierte documentos
- detecta tablas
- aporta contexto narrativo básico
- luego el sistema se apoya demasiado rápido en un DataFrame seleccionado

Ese diseño fue correcto para llegar a un MVP, pero limita el diferencial del producto.

## Estado objetivo

El activo central de una sesión debe ser el **documento estructurado**, no solo la tabla elegida.

### Flujo objetivo

1. archivo subido
2. procesamiento con Docling
3. persistencia de `DoclingDocument`
4. extracción de:
   - tablas
   - narrativa
   - metadatos estructurales
   - referencias de origen
5. chunking semántico
6. findings y query sobre:
   - findings
   - tablas
   - narrativa
   - chunks
7. respuestas con evidencia verificable

## Capacidades Docling que deben entrar en Data-X

### 1. Documento estructurado completo
Guardar `DoclingDocument.export_to_dict()` o equivalente persistible.

### 2. Multi-tabla real
No quedarse con una tabla. Guardar y explotar todas las tablas relevantes.

### 3. Narrativa documental
Usar `doc.texts` y/o equivalente para preguntas sobre:
- riesgos
- notas
- observaciones
- explicaciones del documento

### 4. Chunking semántico
Adoptar `HybridChunker` o estrategia equivalente para:
- RAG documental
- recuperación más fiel
- trazabilidad por chunk

### 5. Provenance
Cada finding importante debe poder señalar:
- archivo
- página
- sección
- tabla
- fila o chunk cuando aplique

## Qué no hacer

- aplanar el documento demasiado temprano
- tratar Docling como una librería auxiliar más
- construir nuevas features sobre un modelo documental incompleto
- mover a microservicios antes de consolidar el modelo documental local

## Orden correcto

### Ahora
- persistencia documental
- multi-tabla
- chunks
- provenance
- RAG documental

### Después
- explorer documental más rico
- desacople operativo
- jobs/colas
- `docling-serve` si hace falta

### Mucho después
- `docling-graph`
- grafos semánticos
- escala enterprise documental

## Regla de producto

Toda decisión nueva debe responder:

> ¿Estamos reforzando a Docling como subsistema central, o lo estamos reduciendo otra vez a un parser de apoyo?

Si la respuesta es la segunda, la decisión es incorrecta.
