import litellm
from app.core.config import settings
import structlog
import json
from typing import Optional

logger = structlog.get_logger(__name__)

class LLMService:
    def __init__(self):
        self.model = settings.litellm_model
        self.api_key = settings.litellm_api_key
        # Configurar litellm
        litellm.api_key = self.api_key

    async def generate_explanation(self, finding: dict, dataset_context: dict) -> str:
        """
        Genera una explicación enriquecida para un Finding usando LiteLLM.
        Si falla, devuelve la explicación estática del finding.
        """
        if not self.api_key:
            return finding.get("explanation", "No hay explicación disponible.")

        try:
            prompt = f"""
            Eres un experto analista de datos. Explica el siguiente hallazgo (Finding) de un dataset.
            Contexto del dataset: {json.dumps(dataset_context, default=str)}
            Hallazgo: {json.dumps(finding, default=str)}
            Explica el problema en lenguaje claro para un usuario no técnico, indicando por qué es importante y qué impacto tiene.
            Responde solo con la explicación, sin encabezados ni introducciones.
            """
            
            response = await litellm.acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=30,
                num_retries=1
            )
            explanation = response.choices[0].message.content.strip()
            logger.info("llm_explanation_generated", finding_id=finding.get("finding_id"))
            return explanation
        except Exception as e:
            logger.error("llm_explanation_failed", error=str(e), finding_id=finding.get("finding_id"))
            return finding.get("explanation", "Error al generar explicación inteligente.")

    async def generate_executive_summary(self, report_data: dict) -> str:
        """
        Genera un resumen ejecutivo del dataset de 3 a 5 oraciones.
        """
        if not self.api_key:
            overview = report_data.get("dataset_overview", {})
            return f"El dataset contiene {overview.get('row_count', 0)} filas y {overview.get('column_count', 0)} columnas. Se detectaron {len(report_data.get('findings', []))} hallazgos importantes."

        try:
            prompt = f"""
            Genera un resumen ejecutivo de 3 a 5 oraciones basado en este análisis de datos:
            {json.dumps(report_data, default=str)}
            Sé conciso y resalta los puntos clave sobre la calidad y el contenido del dataset.
            """
            
            response = await litellm.acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=30,
                num_retries=1
            )
            summary = response.choices[0].message.content.strip()
            logger.info("llm_summary_generated")
            return summary
        except Exception as e:
            logger.error("llm_summary_failed", error=str(e))
            overview = report_data.get("dataset_overview", {})
            return f"Análisis completado. El dataset tiene {overview.get('row_count', 0)} registros con {len(report_data.get('findings', []))} alertas detectadas."

    async def answer_query(self, query: str, session_context: dict) -> dict:
        """
        Responde preguntas sobre el dataset basadas en el contexto de la sesión.
        """
        if not self.api_key:
            return {
                "answer": "LLM no configurado. Por favor, revisa los hallazgos del análisis manual.",
                "relevant_findings": [],
                "confidence": "n/a"
            }

        try:
            prompt = f"""
            Eres un asistente de análisis de datos de Data-X. Responde a la consulta del usuario basándote en el contexto del análisis.
            Contexto: {json.dumps(session_context, default=str)}
            Consulta: {query}
            
            Devuelve un JSON estrictamente con este formato:
            {{
              "answer": "Tu respuesta explicativa",
              "relevant_findings": ["id_hallazgo_1", "id_hallazgo_2"],
              "confidence": "high|medium|low"
            }}
            """
            
            response = await litellm.acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=30,
                num_retries=1,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            logger.info("llm_query_answered", query=query)
            return result
        except Exception as e:
            logger.error("llm_query_failed", error=str(e), query=query)
            return {
                "answer": "No se pudo procesar la consulta inteligente en este momento.",
                "relevant_findings": [],
                "confidence": "low"
            }
