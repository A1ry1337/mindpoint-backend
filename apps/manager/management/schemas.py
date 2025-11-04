from typing import List, Optional
from uuid import UUID
from datetime import date
from ninja import Schema
from pydantic import BaseModel

class TeamOut(BaseModel):
    id: UUID
    name: str

class EmployeeOut(BaseModel):
    id: UUID
    username: str
    fullname: str
    team: Optional[TeamOut]
    is_teamlead: Optional[bool]

class TeamIn(Schema):
    name: str

class AddMembersIn(Schema):
    team_id: str
    user_ids: List[str]

class Dass9DayAvgOut(Schema):
    date: date
    depression_avg: float
    stress_avg: float
    anxiety_avg: float


class TeamDass9ResultOut(Schema):
    team: str
    results: List[Dass9DayAvgOut]

class TeamLeadIn(Schema):
    user_id: str

class MemberOut(Schema):
    id: UUID
    username: str
    fullname: str
    is_teamlead: Optional[bool]

class TeamWithMembersOut(Schema):
    team: TeamOut
    members: List[MemberOut]
    team_leads: List[MemberOut]

class AssignTeamLeadIn(Schema):
    team_id: str
    user_id: str

class ManagerRequestResponseIn(Schema):
    request_id: str
    approve: bool

class RemoveMemberFromTeamIn(Schema):
    team_id: str
    user_id: str

class MoveMemberToAnotherTeamIn(Schema):
    user_id: str
    from_team_id: str
    to_team_id: str
