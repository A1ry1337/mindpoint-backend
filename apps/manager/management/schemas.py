from typing import List
from uuid import UUID

from ninja import Schema
from pydantic import BaseModel

class EmployeeOut(BaseModel):
    id: UUID
    username: str
    fullname: str

class TeamIn(Schema):
    name: str

class AddMembersIn(Schema):
    team_id: str
    user_ids: List[str]
