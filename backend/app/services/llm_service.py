import litellm
from litellm import Router, completion_cost
from app.core.config import settings
import structlog
import json
import os
from typing import Optional, Any

logger = structlog.get_logger(__name__)

# Configurar cache distribuido en Redis
redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = os.environ.get("REDIS_PORT", "6379")
litellm.cache = litellm.Cache(type="redis", host=redis_host, port=redis_port)

class LLMService:
    def __init__(self):
        self.api_key = settings.litellm_api_key
        self.router = None
        if self.api_key:
            model_list = [
                {
                    "model_name": "default",
                    "litellm_params": {
                        "model": settings.litellm_model,
                        "api_key": self.api_key,
                    }
                }
            ]
            # Podríamos agregar fallbacks adicionales aquí si estuvieran en config
            self.router = Router(
                model_list=model_list,
                num_retries=2,
                timeout=30,
                retry_after=2,
            )

    async def generate_enriched_explanation(self, finding: Any, dataset_context: dict) -> dict:
        """
        NUEVO método que toma un Finding determinístico y genera una explicación
        contextualizada para el dataset específico.
        """
        if not self.router:
            return {"explanation": None, "cost_usd": 0.0}

        try:
            filename = dataset_context.get("original_filename", "dataset")
            rows = dataset_context.get("row_count", 0)
            cols = dataset_context.get("column_count", 0)
            narrative = dataset_context.get("narrative_context", "")
            
            # En Pydantic v2 o dict, tratamos de acceder a los campos
            f_what = getattr(finding, "what", finding.get("what", "")) if not isinstance(finding, dict) else finding.get("what", "")
            f_so_what = getattr(finding, "so_what", finding.get("so_what", "")) if not isinstance(finding, dict) else finding.get("so_what", "")
            f_now_what = getattr(finding, "now_what", finding.get("now_what", "")) if not isinstance(finding, dict) else finding.get("now_what", "")

            prompt = f"""Sos un analista de datos explicando resultados a una persona de negocio.
Te doy un hallazgo de un análisis de datos. Tu trabajo es explicar
POR QUÉ este hallazgo es importante para ESTE dataset específico
y QUÉ debería hacer el usuario.

Dataset: {filename}, {rows} filas, {cols} columnas
{f"Contexto del documento: {narrative[:2000]}" if narrative else ""}

Hallazgo:
- Qué encontramos: {f_what}
- Por qué importa: {f_so_what}
- Qué hacer: {f_now_what}

Generá una explicación de 2-3 oraciones que contextualice este hallazgo
para ESTE dataset específico. Sé concreto, mencioná nombres de columnas
y valores reales. No repitas lo que ya dice el hallazgo, agregá valor."""

            response = await self.router.acompletion(
                model="default",
                messages=[{"role": "user", "content": prompt}]
            )
            
            explanation = response.choices[0].message.content.strip()
            cost = completion_cost(completion_response=response) or 0.0
            
            return {
                "explanation": explanation,
                "cost_usd": cost,
                "model": getattr(response, "model", settings.litellm_model)
            }
        except Exception as e:
            logger.error("llm_enriched_explanation_failed", error=str(e))
            return {"explanation": None, "cost_usd": 0.0}

    async def generate_executive_summary(self, report_data: dict) -> dict:
        """
        Genera un resumen ejecutivo orientado a acción.
        """
        if not self.router:
            overview = report_data.get("dataset_overview", {})
            return {
                "summary": f"Análisis completado. El dataset tiene {overview.get('row_count', 0)} registros con {len(report_data.get('findings', []))} alertas detectadas.",
                "cost_usd": 0.0
            }

        try:
            prompt = """Sos un analista de datos presentando resultados a un directivo.
Resumí los hallazgos de este dataset en 3-5 oraciones.
Enfocate en: qué puede hacer esta persona con estos datos,
qué riesgos hay, y qué oportunidades se detectaron.
No uses jerga técnica. Sé directo y accionable."""

            findings_summary = "\n".join([
                f"- {getattr(f, 'title', f.get('title')) if not isinstance(f, dict) else f.get('title')}: {getattr(f, 'what', f.get('what')) if not isinstance(f, dict) else f.get('what')}" 
                for f in report_data.get("findings", [])[:5]
            ])

            response = await self.router.acompletion(
                model="default",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Hallazgos detectados:\n{findings_summary}"}
                ]
            )
            
            summary = response.choices[0].message.content.strip()
            cost = completion_cost(completion_response=response) or 0.0
            
            return {
                "summary": summary,
                "cost_usd": cost,
                "model": getattr(response, "model", settings.litellm_model)
            }
        except Exception as e:
            logger.error("llm_summary_failed", error=str(e))
            return {"summary": "Error al generar resumen inteligente.", "cost_usd": 0.0}

    async def answer_query(self, query: str, relevant_findings: list, context_sources: Optional[list[dict]] = None) -> dict:
        """
        Responde preguntas usando contexto RAG (findings relevantes).
        Retorna JSON estructurado.
        """
        if not self.router:
            return {
                "answer": "Servicio de IA no configurado.",
                "confidence": "low",
                "sources_used": [],
                "cost_usd": 0.0
            }

        try:
            findings_text = "\n".join([
                f"- {f.title if not isinstance(f, dict) else f.get('title')}: {f.what if not isinstance(f, dict) else f.get('what')} (ID: {f.finding_id if not isinstance(f, dict) else f.get('finding_id')}, Impacto: {f.so_what if not isinstance(f, dict) else f.get('so_what')})" 
                for f in relevant_findings
            ])

            source_context = ""
            if context_sources:
                source_lines = []
                for source in context_sources[:10]:
                    source_lines.append(
                        f"- [{source.get('source_type', 'unknown')}] {source.get('source_id', '')}: {source.get('snippet', '')}"
                    )
                source_context = "\nFuentes documentales recuperadas:\n" + "\n".join(source_lines)

            system_prompt = """Sos un analista de datos experto. Respondé basándote EXCLUSIVAMENTE
en los hallazgos y fuentes documentales que te doy. No inventes datos.
Si la pregunta no se puede responder con estas fuentes, decilo honestamente.

Respondé SOLO con un objeto JSON con esta estructura exacta:
{
  "answer": "tu respuesta detallada pero clara en lenguaje de negocio",
  "confidence": "high|medium|low",
  "sources_used": [
    {"source_type":"finding|chunk|table|section|page_reference","source_id":"id","evidence_ref":"ref opcional"}
  ]
}"""

            user_content = f"Hallazgos relevantes:\n{findings_text}{source_context}\n\nPregunta del usuario: {query}"

            response = await self.router.acompletion(
                model="default",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            try:
                structured_data = json.loads(content)
            except Exception:
                # Fallback si no es JSON válido
                return {
                    "answer": content,
                    "confidence": "medium",
                    "sources_used": [],
                    "cost_usd": completion_cost(completion_response=response) or 0.0,
                    "model": getattr(response, "model", settings.litellm_model)
                }
            
            return {
                "answer": structured_data.get("answer", content),
                "confidence": structured_data.get("confidence", "medium"),
                "sources_used": structured_data.get("sources_used", []),
                "cost_usd": completion_cost(completion_response=response) or 0.0,
                "model": getattr(response, "model", settings.litellm_model)
            }
        except Exception as e:
            logger.error("llm_query_failed", error=str(e))
            return {"answer": f"Error al procesar la consulta: {str(e)}", "cost_usd": 0.0}

    async def generate_recommendations(self, findings: list) -> dict:
        """
        Genera una lista de 3-5 recomendaciones accionables basadas en los findings.
        """
        if not self.router or not findings:
            # Fallback determinístico
            critical = [f for f in findings if (f.severity if not isinstance(f, dict) else f.get('severity')) == 'critical']
            data_gaps = [f for f in findings if (f.category if not isinstance(f, dict) else f.get('category')) == 'data_gap']
            
            recs = []
            if critical:
                recs.append("Revisar urgentemente los problemas críticos antes de usar estos datos para decisiones.")
            if data_gaps:
                recs.append("Completar los datos faltantes en las columnas afectadas para mejorar la calidad del análisis.")
            
            if len(recs) < 3:
                recs.append("Investigar los patrones detectados para validar hipótesis de negocio.")
                recs.append("Los datos están en buena forma general, pero se recomienda monitoreo continuo.")
            
            return {
                "recommendations": recs[:5],
                "cost_usd": 0.0
            }

        try:
            findings_text = "\n".join([
                f"- {f.title if not isinstance(f, dict) else f.get('title')}: {f.what if not isinstance(f, dict) else f.get('what')}" 
                for f in findings[:10]
            ])

            prompt = f"""Basándote en estos hallazgos de un análisis de datos, generá 3-5 recomendaciones ACCIONABLES.
Cada recomendación debe ser una oración corta y concreta que el usuario pueda ejecutar. No uses jerga técnica.

Hallazgos:
{findings_text}

Respondé SOLO con la lista de recomendaciones, una por línea, empezando con un guión."""

            response = await self.router.acompletion(
                model="default",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.choices[0].message.content.strip()
            # Parsear líneas que empiecen con guión o número
            lines = [line.strip().lstrip('- ').lstrip('123456789. ') for line in content.split('\n') if line.strip()]
            cost = completion_cost(completion_response=response) or 0.0
            
            return {
                "recommendations": lines[:5],
                "cost_usd": cost,
                "model": getattr(response, "model", settings.litellm_model)
            }
        except Exception as e:
            logger.error("llm_recommendations_failed", error=str(e))
            return {
                "recommendations": ["Revisar los hallazgos detallados en el reporte."],
                "cost_usd": 0.0
            }
