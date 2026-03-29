from abc import ABC, abstractmethod
from typing import Any, List


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
