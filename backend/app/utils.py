"""
Utilidades compartidas para el proyecto Data-X.

ACT-013: Helper _to_dict() para normalizar objetos Finding/Pydantic/dict
a un dict puro, eliminando el patrón duplicado en llm_service.py.
"""
from typing import Any


def to_dict(obj: Any) -> dict:
    """
    Normaliza un objeto Pydantic v2, Pydantic v1, dataclass o dict a dict puro.

    Antes (patrón repetido 15+ veces en llm_service.py):
        f.title if not isinstance(f, dict) else f.get('title')

    Después:
        f = to_dict(finding)
        f.get('title')
    """
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):      # Pydantic v2
        return obj.model_dump()
    if hasattr(obj, "dict"):            # Pydantic v1
        return obj.dict()
    if hasattr(obj, "__dataclass_fields__"):  # dataclass
        import dataclasses
        return dataclasses.asdict(obj)
    return vars(obj)
