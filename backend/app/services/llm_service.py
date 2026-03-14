import litellm
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

class LLMService:
    def __init__(self):
        self.model = settings.litellm_model
        self.api_key = settings.litellm_api_key

    async def generate_summary(self, filename: str, profile: dict) -> str:
        """
        Genera un resumen narrativo del dataset basado en su perfil.
        """
        prompt = f"""
        Analiza el siguiente perfil de un dataset llamado '{filename}' y genera un resumen ejecutivo breve (máximo 4 oraciones).
        Menciona la cantidad de datos, los tipos de columnas más relevantes y cualquier anomalía o dato interesante (como nulos o cardinalidad).
        
        Perfil del dataset:
        {profile}
        
        Responde en español, tono profesional y directo.
        """
        
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                api_key=self.api_key
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Error al generar resumen con LLM", error=str(e))
            # Fallback a resumen básico si falla el LLM
            num_rows = next(iter(profile.values()))["count"] if profile else 0
            return f"Dataset '{filename}' con {num_rows} filas. (Resumen automático limitado)"

    async def analyze_query(self, query: str, profile: dict) -> str:
        """
        Responde a una consulta específica sobre el dataset usando el perfil.
        """
        prompt = f"""
        Eres un experto analista de datos. Responde a la siguiente consulta sobre un dataset basándote solo en su perfil estadístico.
        
        Consulta: "{query}"
        
        Perfil estadístico:
        {profile}
        
        Instrucciones:
        - Si la consulta es general, destaca lo más importante.
        - Si preguntan por algo que no está en el perfil, aclara las limitaciones.
        - Sé conciso y técnico pero accesible.
        """
        
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                api_key=self.api_key
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Error en consulta LLM", error=str(e))
            return "No se pudo procesar la consulta inteligente en este momento."
