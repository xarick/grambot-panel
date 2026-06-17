from datetime import datetime

from pydantic import BaseModel, Field

TEXT_LIMIT = 4096
CAPTION_LIMIT = 1024
BUTTON_TEXT_LIMIT = 64
MAX_BUTTONS = 8


class BroadcastButton(BaseModel):
    text: str
    url: str


class BroadcastCreate(BaseModel):
    bot_id: int
    text: str = Field(default="", max_length=TEXT_LIMIT)
    scheduled_at: datetime | None = None
    segment_tag: str = ""
    media_type: str = ""
    media_path: str = ""
    buttons: list[BroadcastButton] = Field(default_factory=list, max_length=MAX_BUTTONS)


class RecipientCountOut(BaseModel):
    bot_id: int
    count: int


class MediaUploadOut(BaseModel):
    media_type: str
    media_path: str


class BroadcastOut(BaseModel):
    id: int
    bot_id: int | None
    text: str
    status: str
    scheduled_at: datetime | None
    media_type: str
    segment_tag: str
    total_recipients: int
    sent_count: int
    failed_count: int
    created_by_id: int | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class BroadcastListOut(BaseModel):
    items: list[BroadcastOut]
    total: int
