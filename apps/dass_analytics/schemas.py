from ninja import Schema
from typing import Optional, Literal


class ChangeSchema(Schema):
    direction: Literal["up", "down", "neutral"]
    percent: Optional[float]


class IpsStatisticsOut(Schema):
    period: Literal["day", "week", "month", "year"]
    ips_score: float
    ips_max_score: float
    change: ChangeSchema
