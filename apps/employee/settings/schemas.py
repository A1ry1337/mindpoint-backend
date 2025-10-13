from ninja import Schema
from uuid import UUID

class ManagerAssignmentRequestByNameIn(Schema):
    manager_username: str

class ManagerAssignmentRequestOut(Schema):
    request_id: UUID
    manager_username: str
    status: str
    created_at: str
