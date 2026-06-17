from pydantic import BaseModel


class DayPoint(BaseModel):
    date: str
    new_subscribers: int
    messages_in: int
    messages_out: int


class TopBot(BaseModel):
    bot_id: int
    name: str
    messages: int


class Totals(BaseModel):
    subscribers: int
    messages: int
    bots: int
    new_subscribers_period: int


class StatsOut(BaseModel):
    days: int
    series: list[DayPoint]
    top_bots: list[TopBot]
    totals: Totals
