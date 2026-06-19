from datetime import datetime

from pydantic import BaseModel


class TelegramUserOut(BaseModel):
    id: int
    telegram_id: int
    username: str
    first_name: str
    last_name: str
    full_name: str
    language_code: str
    is_blocked: bool

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: int
    bot_id: int
    is_open: bool
    tag: str | None
    last_message_at: datetime | None
    created_at: datetime
    unread_count: int = 0
    user: TelegramUserOut

    model_config = {"from_attributes": True}


class ConversationListOut(BaseModel):
    items: list[ConversationOut]
    total: int


class ConversationUpdate(BaseModel):
    is_open: bool | None = None
    tag: str | None = None


class BlockUserRequest(BaseModel):
    is_blocked: bool


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    direction: str
    telegram_message_id: int | None
    text: str
    message_type: str
    file_id: str
    file_name: str
    sent_at: datetime
    is_read: bool
    sent_by_id: int | None

    model_config = {"from_attributes": True}


class MessageListOut(BaseModel):
    items: list[MessageOut]
    has_more: bool


class ReplyRequest(BaseModel):
    text: str
