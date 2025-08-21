from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreateSchema(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str
    full_name: Optional[str] = None

class UserReadSchema(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

    class Config:
        orm_mode = True

class TokenSchema(BaseModel):
    access: str

class TokenRefreshSchema(BaseModel):
    refresh: str
