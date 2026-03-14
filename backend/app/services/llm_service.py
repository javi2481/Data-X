# LLMService disponible para Corte 2. Desactivado en Corte 1.
# import litellm
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

class LLMService:
    def __init__(self):
        # self.model = settings.litellm_model
        # self.api_key = settings.litellm_api_key
        pass

    async def generate_summary(self, filename: str, profile: dict) -> str:
        """
        LLMService desactivado en Corte 1.
        """
        return f"Dataset '{filename}' analizado. (Resumen estático - Corte 1)"

    async def analyze_query(self, query: str, profile: dict) -> str:
        """
        LLMService desactivado en Corte 1.
        """
        return "Respuesta estática: El servicio de análisis inteligente (LLM) está desactivado en esta versión."
