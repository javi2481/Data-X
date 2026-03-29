from pydantic import BaseModel
from typing import Dict
from app.schemas.medallion import ColumnProfile


class ProfilingSummary(BaseModel):
    columns: Dict[str, ColumnProfile]
