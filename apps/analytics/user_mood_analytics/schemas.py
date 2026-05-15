from datetime import date
from typing import List, Literal

from ninja import Schema


class UserMoodScorePercentOut(Schema):
    score: int
    count: int
    percent: float


class UserMoodPointOut(Schema):
    """
    Одна точка графика.

    week:
        label = "2025-04-13"
        start_date == end_date
        score = score за конкретный день

    month:
        label = "Неделя 1"
        start_date / end_date = границы недели
        score = средний score за неделю

    year:
        label = "Апр 2025"
        start_date / end_date = границы месяца
        score = средний score за месяц

    Если данных за период нет, score = 0.0.
    """
    label: str
    start_date: date
    end_date: date
    score: float


class UserMoodHistoryOut(Schema):
    period: Literal["week", "month", "year"]

    total_completions: int
    score_distribution: List[UserMoodScorePercentOut]

    rec_mood_trigger: bool
    consecutive_low_trigger: bool

    # Количество точек:
    # week  -> 7
    # month -> 4
    # year  -> 12
    points: List[UserMoodPointOut]