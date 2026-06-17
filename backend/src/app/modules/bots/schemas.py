from datetime import datetime

from pydantic import BaseModel


class BotCreate(BaseModel):
    name: str
    token: str


class BotUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    webhook_base_url: str | None = None


class BotOut(BaseModel):
    id: int
    name: str
    token: str
    username: str
    is_active: bool
    webhook_base_url: str = ""
    webhook_url: str = ""
    created_at: datetime
    user_count: int = 0
    open_conversation_count: int = 0
    unread_count: int = 0

    model_config = {"from_attributes": True}


class BotChatOut(BaseModel):
    id: int
    chat_id: int
    type: str
    title: str
    username: str
    bot_status: str
    added_at: datetime
    synced_at: datetime | None = None

    model_config = {"from_attributes": True}


class ChatAdmin(BaseModel):
    id: int
    username: str
    name: str
    status: str
    is_bot: bool


class ChatLiveInfo(BaseModel):
    chat_id: int
    title: str
    type: str
    username: str
    description: str
    member_count: int | None
    bot_status: str
    admins: list[ChatAdmin]
    synced_at: datetime | None = None
