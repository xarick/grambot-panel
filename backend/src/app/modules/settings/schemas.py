from pydantic import BaseModel


class SettingsOut(BaseModel):
    webhook_base_url: str


class SettingsUpdate(BaseModel):
    webhook_base_url: str
