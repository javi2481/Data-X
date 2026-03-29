import litellm
from litellm import Router, completion_cost
from app.core.config import settings
from app.utils import to_dict
import structlog
import json
from typing import Optional, Any, List, Dict
import re

logger = structlog.get_logger(__name__)

# NXT-004: Anti-hallucination guardrails threshold
HALLUCINATION_RISK_THRESHOLD = 0.5

class LLMService:
    def __init__(self):
        self.api_key = settings.litellm_api_key

        # ── BUG-004 fix: inicializar cache Redis dentro del constructor ────────
        # Antes: litellm.cache se inicializaba a nivel de módulo con os.environ,
        # ignorando el sistema de configuración centralizado (Settings/Pydantic).
        # Esto causaba inconsistencias en Docker/K8s donde Redis corre en un host
        # diferente al configurado en settings.
        try:
            litellm.cache = litellm.Cache(
                type="redis",
                host=settings.redis_host,
                port=settings.redis_port,
            )
        except Exception as e:
            logger.warning("litellm_cache_unavailable", error=str(e))
            litellm.cache = None  # Degradar graciosamente si Redis no está disponible
        # ─────────────────────────────────────────────────────────────────────

        self.router = None
        if self.api_key:
            # Modelo primario
            model_list = [
                {
                    "model_name": "primary",
                    "litellm_params": {
                        "model": settings.litellm_model,
                        "api_key": self.api_key,
                    }
                }
            ]
            # ACT-007: agregar fallback si está configurado en settings
            # Elimina el punto único de falla: si OpenRouter cae, el Router
            # hace failover automático al modelo de fallback configurado.
            fallbacks = []
            if settings.litellm_fallback_model:
                model_list.append({
                    "model_name": "fallback",
                    "litellm_params": {
                        "model": settings.litellm_fallback_model,
                        "api_key": self.api_key,
                    }
                })
                fallbacks = [{"primary": ["fallback"]}]
                logger.info("litellm_fallback_configured", model=settings.litellm_fallback_model)

            self.router = Router(
                model_list=model_list,
                fallbacks=fallbacks,
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

            # ACT-013: normalizar finding a dict una sola vez (elimina 15+ getattr ternarios)
            f = to_dict(finding)
            f_what    = f.get("what", "")
            f_so_what = f.get("so_what", "")
            f_now_what = f.get("now_what", "")

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

    async def answer_query(self, query: str, relevant_findings: list, context_sources: Optional[list[dict]] = None, available_source_map: Optional[Dict[str, Any]] = None) -> dict:
        """
        Responde preguntas usando contexto RAG (findings relevantes).
        Retorna JSON estructurado con guardrails anti-alucinación (NXT-004).
        """
        if not self.router:
            return {
                "answer": "Servicio de IA no configurado.",
                "confidence": "low",
                "sources_used": [],
                "hallucination_risk": 0.0,
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

            # NXT-004: Prompt mejorado con reglas estrictas anti-alucinación
            system_prompt = """Sos un analista de datos experto. Respondé basándote EXCLUSIVAMENTE
en los hallazgos y fuentes documentales que te doy. No inventes datos.
Si la pregunta no se puede responder con estas fuentes, decilo honestamente.

REGLAS ESTRICTAS:
1. SIEMPRE cita el source_id exacto de donde sacaste cada información.
2. Si no tenés suficiente información, decí "No tengo suficiente información para responder."
3. No hagas suposiciones ni generalizaciones sin evidencia directa.
4. Si un número o estadística no aparece en las fuentes, NO lo inventes.

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
                    "hallucination_risk": 0.5,  # Penalizar respuestas malformadas
                    "warning": "La respuesta no pudo ser validada correctamente.",
                    "cost_usd": completion_cost(completion_response=response) or 0.0,
                    "model": getattr(response, "model", settings.litellm_model)
                }
            
            answer = structured_data.get("answer", content)
            confidence = structured_data.get("confidence", "medium")
            sources_used = structured_data.get("sources_used", [])
            
            # NXT-004: Calcular hallucination risk
            source_map = available_source_map or {}
            hallucination_risk = self._calculate_hallucination_risk(
                confidence=confidence,
                sources_used=sources_used,
                answer=answer,
                available_source_map=source_map
            )
            
            # Si risk >= threshold, rechazar respuesta
            warning = None
            if hallucination_risk >= HALLUCINATION_RISK_THRESHOLD:
                warning = "Esta respuesta tiene alta probabilidad de ser inexacta. Verifica los hallazgos manualmente."
                logger.warning(
                    "high_hallucination_risk",
                    query=query[:50],
                    risk=hallucination_risk,
                    confidence=confidence,
                    sources_count=len(sources_used)
                )
                # Reemplazar con respuesta genérica segura
                answer = "No puedo responder con certeza basado en las fuentes disponibles. Por favor, revisa los hallazgos manualmente en el reporte."
                confidence = "low"
            elif hallucination_risk >= 0.3:
                warning = "Esta respuesta tiene baja confianza. Verifica los hallazgos si necesitas mayor precisión."
            
            return {
                "answer": answer,
                "confidence": confidence,
                "sources_used": sources_used,
                "hallucination_risk": hallucination_risk,
                "warning": warning,
                "cost_usd": completion_cost(completion_response=response) or 0.0,
                "model": getattr(response, "model", settings.litellm_model)
            }
        except Exception as e:
            logger.error("llm_query_failed", error=str(e))
            return {
                "answer": f"Error al procesar la consulta: {str(e)}",
                "confidence": "low",
                "hallucination_risk": 1.0,
                "warning": "Error técnico al procesar la respuesta.",
                "cost_usd": 0.0
            }

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


    # ── NXT-004: Anti-hallucination guardrails ──────────────────────────────
    
    def _verify_sources_exist(
        self,
        sources_used: List[Dict[str, Any]],
        available_source_map: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Verifica que las fuentes citadas por el LLM existan en source_map.
        
        Returns:
            (all_valid, invalid_ids)
        """
        invalid_ids = []
        
        for source in sources_used:
            source_id = source.get("source_id", "")
            if source_id and source_id not in available_source_map:
                invalid_ids.append(source_id)
        
        return len(invalid_ids) == 0, invalid_ids
    
    def _calculate_hallucination_risk(
        self,
        confidence: str,
        sources_used: List[Dict[str, Any]],
        answer: str,
        available_source_map: Dict[str, Any]
    ) -> float:
        """
        Calcula el score de riesgo de alucinación (0.0 - 1.0).
        
        Factores:
        - Fuentes inventadas: +0.4 (grave)
        - Confidence low: +0.3
        - Confidence medium: +0.1
        - Sin fuentes: +0.2
        - Respuesta muy corta (< 50 chars): +0.1
        
        Score:
            0.0 - 0.3: Respuesta confiable ✅
            0.3 - 0.5: Baja confianza ⚠️
            0.5 - 1.0: Alta probabilidad de alucinación ❌
        """
        risk = 0.0
        
        # Factor 1: Fuentes inventadas (GRAVE)
        all_valid, invalid_ids = self._verify_sources_exist(sources_used, available_source_map)
        if not all_valid:
            risk += 0.4
            logger.warning(
                "sources_verification_failed",
                invalid_ids=invalid_ids,
                msg="LLM cited non-existent sources"
            )
        
        # Factor 2: Confianza baja del LLM
        if confidence == "low":
            risk += 0.3
        elif confidence == "medium":
            risk += 0.1
        
        # Factor 3: Sin fuentes citadas
        if len(sources_used) == 0:
            risk += 0.2
        
        # Factor 4: Respuesta muy corta (indica vaguedad)
        if len(answer) < 50:
            risk += 0.1
        
        return min(risk, 1.0)  # Cap at 1.0
    
    # ─────────────────────────────────────────────────────────────────────────
