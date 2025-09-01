from ninja import Schema
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreateSchema(BaseModel):
    username: str
    managerId: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str
    full_name: Optional[str] = None

class LoginResponse(Schema):
    access: str
    userId: str
    username: str
    fullname: str
    isManager: bool
