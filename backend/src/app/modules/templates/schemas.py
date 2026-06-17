from datetime import datetime

from pydantic import BaseModel


class TemplateCreate(BaseModel):
    title: str
    text: str


class TemplateUpdate(BaseModel):
    title: str | None = None
    text: str | None = None


class TemplateOut(BaseModel):
    id: int
    title: str
    text: str
    created_by_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
