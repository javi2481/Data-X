---
name: principio_interpretabilidad
description: Data-X muestra consecuencias de negocio, nunca métricas técnicas al usuario
type: feedback
---

El usuario no necesita saber cuántas columnas tiene su archivo ni el porcentaje de nulos.
Necesita saber qué significan esos datos para la decisión que tiene que tomar.

**Why:** Los conteos técnicos (filas, columnas, nulos, tipos de datos, scores) son internos.
El producto es la interpretación, no el análisis.

**How to apply:**
- Los mensajes de progreso hablan de valor ("Buscando problemas que afectan tus decisiones"), no de estructura ("Encontré 8 columnas")
- Los findings muestran enriched_explanation primero (consecuencia de negocio), los campos técnicos son detalle expandible
- Los prompts de LLM deben pedir "consecuencia para la decisión", nunca "explicación del hallazgo estadístico"
- Nunca mostrar al usuario: cantidad de columnas/filas, % nulos, tipos de datos, nombres de tests estadísticos
- El resumen ejecutivo responde "¿qué hago?" no "qué encontramos"
