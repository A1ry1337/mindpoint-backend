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
    period: Literal["week", "month", "year"]
    recommendation_trigger: bool
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
    recommendation_trigger: bool
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

class SeverityLevelSchema(Schema):
    members: int
    percent: Optional[float]

class SeverityMetricSchema(Schema):
    Normal: SeverityLevelSchema
    Mild: SeverityLevelSchema
    Moderate: SeverityLevelSchema
    High: SeverityLevelSchema
    Very_High: SeverityLevelSchema

class TeamSeveritySchema(Schema):
    team_id: str
    team_name: str
    recommendation_trigger: bool
    total_members: int
    depression: SeverityMetricSchema
    anxiety: SeverityMetricSchema
    stress: SeverityMetricSchema

class SeverityTeamsOut(Schema):
    teams: List[TeamSeveritySchema]

class SeverityTeamsIn(Schema):
    team_ids: Optional[List[str]] = None
    period: Literal["day", "week", "month", "year"] = "day"

class PeriodicTestCount(Schema):
    week: int
    month: int
    year: int

class TeamsPeriodicTestCountOut(Schema):
    counts: PeriodicTestCount

class TeamsPeriodicTestCountIn(Schema):
    team_ids: Optional[List[str]] = None

class SeverityLevelSchema(Schema):
    members: int
    percent: float

class PeriodSeverityItem(Schema):
    label: str
    start: str
    end: str
    Normal: SeverityLevelSchema
    Mild: SeverityLevelSchema
    Moderate: SeverityLevelSchema
    High: SeverityLevelSchema
    Very_High: SeverityLevelSchema

class PeriodSeverityResponse(Schema):
    period: Literal["week", "month", "year"]
    depression: List[PeriodSeverityItem]
    anxiety: List[PeriodSeverityItem]
    stress: List[PeriodSeverityItem]

class PeriodSeverityRequest(Schema):
    team_ids: Optional[List[str]] = None
    period: Literal["week", "month", "year"] = "week"

class TeamCoverageSchema(Schema):
    team_id: str
    team_name: str
    total_members: int
    completed_tests: int
    max_possible_tests: int
    coverage_percent: float

class TestingCoverageResponse(Schema):
    period: Literal["week", "month", "year"]
    recommendation_trigger: bool
    teams: List[TeamCoverageSchema]

class TestingCoverageRequest(Schema):
    team_ids: Optional[List[str]] = None
    period: Literal["week", "month", "year"] = "week"