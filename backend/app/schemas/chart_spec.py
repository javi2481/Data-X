from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal

class AxisSpec(BaseModel):
    key: str
    label: str
    type: Literal["categorical", "numeric", "datetime"] = "categorical"

class SeriesSpec(BaseModel):
    key: str
    label: str
    color_hint: Optional[str] = None

class ChartSpec(BaseModel):
    chart_id: str
    chart_type: Literal["bar", "line", "area", "pie", "histogram", "scatter"]
    title: str
    data: List[Dict[str, Any]]
    x_axis: AxisSpec
    y_axis: Optional[AxisSpec] = None
    series: List[SeriesSpec] = []
