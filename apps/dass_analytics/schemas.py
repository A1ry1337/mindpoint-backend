from ninja import Schema
from typing import Optional, Literal, List

class ChangeSchema(Schema):
    direction: Literal["up", "down", "neutral"]
    percent: Optional[float]

class MetricSchema(Schema):
    type: Literal["ips", "anxiety", "depression", "stress"]
    score: float
    max_score: float
    change: ChangeSchema

class MentalStatisticsOut(Schema):
    period: Literal["day", "week", "month", "year"]
    statistics: List[MetricSchema]

class PeriodData(Schema):
    start: str
    end: str
    test_count: int

class TestCountOut(Schema):
    period: Literal["day", "week", "month", "year"]
    periods: List[PeriodData]