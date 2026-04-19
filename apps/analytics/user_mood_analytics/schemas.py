from ninja import Schema
from typing import List, Literal
from datetime import date


class UserMoodScorePercentOut(Schema):
    score: int          # 1–5
    count: int
    percent: float      # процент от общего числа прохождений


class UserMoodPointOut(Schema):
    """
    Одна точка на графике.

    week  → label = "2025-04-13" (конкретная дата), start_date == end_date
    month → label = "Неделя 1",  start_date/end_date — границы 7-дневного окна
    year  → label = "Апр 2025",  start_date/end_date — границы месяца

    score — фактическая оценка (week) или среднее за период (month/year).
    0.0 если прохождений не было.
    """
    label: str
    start_date: date
    end_date: date
    score: float


class UserMoodHistoryOut(Schema):
    period: Literal["week", "month", "year"]

    # Количество прохождений всего за период + проценты по категориям (1–5)
    total_completions: int
    score_distribution: List[UserMoodScorePercentOut]

    # Триггер 1: 60%+ ответов были оценкой 1 или 2
    rec_mood_trigger: bool

    # Триггер 2: есть хотя бы две даты подряд с оценкой <= 2
    consecutive_low_trigger: bool

    # Точки графика: 7 (week) / 31 (month) / 365 (year)
    points: List[UserMoodPointOut]