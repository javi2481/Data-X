from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseIngestionOrchestrator(ABC):
    @abstractmethod
    async def ingest_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        table_index: int = 0,
    ) -> Dict[str, Any]:
        ...
