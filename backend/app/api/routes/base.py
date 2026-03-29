from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseIngestionOrchestrator(ABC):
    """
    Interfaz base (Strategy) para el motor de ingesta y parseo estructural.
    Permite alternar entre una ingesta local (Docling) y una distribuida (IBM Data Prep Kit / Ray).
    """
    
    @abstractmethod
    async def ingest_file(
        self, 
        file_bytes: bytes, 
        filename: str, 
        content_type: str, 
        table_index: int = 0
    ) -> Dict[str, Any]:
        """Procesa un documento estructuralmente y retorna un DataFrame y metadatos unificados."""
        pass