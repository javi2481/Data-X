from abc import ABC, abstractmethod
from typing import Any, List, Dict


class BaseRetrievalService(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @abstractmethod
    def index_findings(self, findings: List[dict]) -> None:
        ...

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[dict]:
        ...

    @abstractmethod
    async def search_hybrid_sources(self, query: str, top_k: int = 8, **filters) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    async def index_hybrid_sources(self, findings: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> None:
        ...
