from ninja import Schema
from typing import Optional, Literal, List
from enum import Enum

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

class CountChangeSchema(Schema):
    direction: Literal["up", "down", "neutral"]
    percent: Optional[float]

class TeamTestComparisonSchema(Schema):
    team_id: str
    team_name: str
    current_count: int
    previous_count: int
    change: CountChangeSchema

class TeamsTestComparisonOut(Schema):
    period: Literal["day", "week", "month", "year"]
    teams: List[TeamTestComparisonSchema]

class TeamsTestComparisonIn(Schema):
    period: Literal["day", "week", "month", "year"] = "week"
    team_ids: Optional[List[str]] = None

class RiskCategorySchema(Schema):
    risk_members: int
    risk_percent: Optional[float]

class RiskTeamSchema(Schema):
    team_id: str
    team_name: str
    total_members: int

    depression: RiskCategorySchema
    anxiety: RiskCategorySchema
    stress: RiskCategorySchema

class RiskTeamsOut(Schema):
    teams: List[RiskTeamSchema]

class RiskTeamsIn(Schema):
    team_ids: Optional[List[str]] = None
    period: Literal["day", "week", "month", "year"] = "day"