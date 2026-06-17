from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    username: str
    is_superuser: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str
    password: str
    is_superuser: bool = False


class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    is_superuser: bool | None = None
    is_active: bool | None = None


class ProfileUpdate(BaseModel):
    username: str | None = None
    current_password: str | None = None
    new_password: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str
