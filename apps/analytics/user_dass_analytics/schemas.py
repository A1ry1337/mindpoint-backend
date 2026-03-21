from ninja import Schema
from typing import List, Optional, Literal


class UserMetricHistoryOut(Schema):
    type: Literal["stress", "anxiety", "depression"]
    score: int
    level: Literal["normal", "moderate", "high"]
    change: Optional[int] = None
    chart: List[int]
    recommendation_trigger: bool


class UserLastDassResultOut(Schema):
    date: str
    statistics: List[UserMetricHistoryOut]