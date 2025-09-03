from uuid import UUID

from pydantic import BaseModel

class EmployeeOut(BaseModel):
    id: UUID
    username: str
    fullname: str