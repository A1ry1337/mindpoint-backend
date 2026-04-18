from ninja import Schema
from typing import List, Optional, Literal
from datetime import date

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


class UserDassCompletionStatsOut(Schema):
    total_tests: int
    completion_percent: float
    recommendation_trigger: bool


class UserDassMetricPointOut(Schema):
    """
    Одна точка на графике.

    week  → label = "2025-04-13" (дата прохождения), start_date == end_date
    month → label = "Неделя 1",  start_date/end_date — границы 7-дневного окна
    year  → label = "Апр 2025",  start_date/end_date — границы месяца

    stress / anxiety / depression — фактическое значение (week) или
    среднее за период (month/year); 0.0 если прохождений не было.
    """
    label: str
    start_date: date
    end_date: date
    stress: float
    anxiety: float
    depression: float


class UserDassHistoryOut(Schema):
    period: Literal["week", "month", "year"]
    stress_recommendation: bool
    anxiety_recommendation: bool
    depression_recommendation: bool
    points: List[UserDassMetricPointOut]