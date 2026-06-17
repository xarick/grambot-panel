from datetime import datetime

from pydantic import BaseModel


class AutoReplyCreate(BaseModel):
    bot_id: int
    keyword: str
    response: str
    match_mode: str = "contains"


class AutoReplyOut(BaseModel):
    id: int
    bot_id: int
    keyword: str
    response: str
    match_mode: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WelcomeUpdate(BaseModel):
    welcome_message: str
