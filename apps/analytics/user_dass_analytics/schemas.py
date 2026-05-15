from datetime import date
from typing import List, Optional, Literal

from ninja import Schema


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
    Одна точка графика DASS9.

    period=week:
    - label = дата, например "2026-05-15"
    - start_date = end_date = дата дня

    period=month:
    - label = "Неделя 1", "Неделя 2", "Неделя 3", "Неделя 4"
    - start_date / end_date = границы недели

    period=year:
    - label = "Янв 2026", "Фев 2026" и т.д.
    - start_date / end_date = границы месяца

    stress / anxiety / depression:
    - среднее значение за период
    - 0.0, если данных за период нет
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