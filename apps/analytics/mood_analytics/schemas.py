from datetime import date
from typing import List, Optional
from uuid import UUID
from ninja import Schema


class MoodScoreCountOut(Schema):
    score: int          # 1-5
    count: int          # сколько ответов с такой оценкой


class MoodPeriodPointOut(Schema):
    period_label: str   # подпись периода (дата или "Неделя 1", "Месяц 3" и т.п.)
    start_date: date
    end_date: date
    total_responses: int
    scores: Optional[List[MoodScoreCountOut]] = None


class TeamMoodStatsOut(Schema):
    team_id: UUID
    recommendation_trigger: bool
    team_name: str
    points: List[MoodPeriodPointOut]


class TeamsMoodRequestIn(Schema):
    period: str                      # "week" | "month" | "year"
    team_id: Optional[UUID] = None   # если не указан — берем все команды менеджера


class TeamsMoodResponseOut(Schema):
    items: List[TeamMoodStatsOut]


class MoodScorePercentOut(Schema):
    score: int          # 1–5
    count: int
    percent: float      # процент людей


class MoodPeriodDistributionOut(Schema):
    period_label: str
    start_date: date
    end_date: date
    total_members: int
    recommendation_trigger: bool
    scores: List[MoodScorePercentOut]


class TeamsMoodDistributionRequestIn(Schema):
    period: str                     # day | week | month | year
    team_ids: Optional[List[UUID]] = None


class TeamsMoodDistributionResponseOut(Schema):
    period: str
    points: List[MoodPeriodDistributionOut]