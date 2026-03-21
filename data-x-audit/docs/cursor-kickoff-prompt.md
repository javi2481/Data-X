# Prompt para comenzar a trabajar con Cursor

Usá este prompt como mensaje inicial en Cursor dentro del repo.

---

Quiero que trabajes sobre este repositorio de Data-X respetando estrictamente estas reglas:

## Contexto estratégico

Data-X ya NO se considera un proyecto verde ni un MVP desde cero.
El repo ya tiene backend, frontend, auth, sesiones, pipeline Bronze/Silver/Gold, findings, reportes, export y query básica.

El problema principal actual NO es hacer más features aisladas.
El problema principal es que Docling todavía está usado de forma parcial.

Hoy el flujo real está demasiado cerca de:
`Docling -> tabla seleccionada -> DataFrame -> findings -> embeddings -> LLM`

El estado objetivo es:
`DoclingDocument completo -> tablas + narrativa + chunks + provenance -> findings + RAG documental + evidencia verificable`

## Tesis del producto

Docling NO es una librería auxiliar.
Docling es el subsistema documental central de Data-X.

## Objetivo inmediato

Quiero que primero entiendas el estado real del repo y luego propongas una ejecución para reconvertir el sistema a una arquitectura Docling-first, sin romper lo que ya funciona.

## Reglas de ownership

- Podés leer todo el repo.
- No modifiques docs todavía, salvo que yo lo pida explícitamente.
- Si proponés cambios de backend, limitate a `backend/`.
- Si proponés cambios de frontend, limitate a `frontend/`.
- No hagas refactors cosméticos.
- No reescribas el sistema desde cero.
- No introduzcas complejidad enterprise prematura.
- No conviertas Docling en un parser secundario.

## Lo que necesito de vos primero

1. Auditá el estado actual del repo.
2. Decime qué partes ya están sólidas y conviene conservar.
3. Detectá exactamente dónde el documento se degrada demasiado temprano a DataFrame.
4. Identificá los archivos concretos donde hay que intervenir primero.
5. Proponé un plan por etapas:
   - hardening
   - persistencia de `DoclingDocument`
   - multi-tabla
   - chunking semántico
   - RAG sobre findings + chunks
   - provenance
   - UX documental
6. No implementes nada todavía hasta que me muestres el plan.

## Formato de respuesta esperado

Quiero una respuesta en este formato:

### 1. Estado actual verificado
### 2. Qué conservar
### 3. Qué cambiar primero
### 4. Riesgos
### 5. Plan de implementación por etapas
### 6. Archivos concretos a tocar primero

Después de eso, recién empezamos a ejecutar.

---
