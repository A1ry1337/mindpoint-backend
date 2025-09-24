from typing import List, Optional
from uuid import UUID

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

class TeamIn(Schema):
    name: str

class AddMembersIn(Schema):
    team_id: str
    user_ids: List[str]
