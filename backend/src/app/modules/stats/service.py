from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.bots.models import TelegramBot, TelegramUser
from app.modules.conversations.models import Conversation, Message


def _date_str(value) -> str:
    if isinstance(value, (datetime,)):
        return value.date().isoformat()
    return str(value)


def get_stats(db: Session, days: int = 14) -> dict:
    days = max(1, min(days, 90))
    since = datetime.now(timezone.utc) - timedelta(days=days - 1)
    start_day = since.date()

    # New subscribers per day
    sub_rows = (
        db.query(func.date(TelegramUser.joined_at), func.count(TelegramUser.id))
        .filter(TelegramUser.joined_at >= since)
        .group_by(func.date(TelegramUser.joined_at))
        .all()
    )
    sub_map = {_date_str(d): int(c) for d, c in sub_rows}

    # Messages per day (by direction)
    msg_rows = (
        db.query(func.date(Message.sent_at), Message.direction, func.count(Message.id))
        .filter(Message.sent_at >= since)
        .group_by(func.date(Message.sent_at), Message.direction)
        .all()
    )
    in_map: dict[str, int] = {}
    out_map: dict[str, int] = {}
    for d, direction, c in msg_rows:
        key = _date_str(d)
        if direction == "incoming":
            in_map[key] = in_map.get(key, 0) + int(c)
        else:
            out_map[key] = out_map.get(key, 0) + int(c)

    series = []
    for i in range(days):
        day = (start_day + timedelta(days=i)).isoformat()
        series.append({
            "date": day,
            "new_subscribers": sub_map.get(day, 0),
            "messages_in": in_map.get(day, 0),
            "messages_out": out_map.get(day, 0),
        })

    # Most active bots (by messages in the window)
    top_rows = (
        db.query(TelegramBot.id, TelegramBot.name, func.count(Message.id))
        .join(Conversation, Conversation.bot_id == TelegramBot.id)
        .join(Message, Message.conversation_id == Conversation.id)
        .filter(Message.sent_at >= since)
        .group_by(TelegramBot.id, TelegramBot.name)
        .order_by(func.count(Message.id).desc())
        .limit(10)
        .all()
    )
    top_bots = [{"bot_id": bid, "name": name, "messages": int(c)} for bid, name, c in top_rows]

    totals = {
        "subscribers": int(db.query(func.count(TelegramUser.id)).scalar() or 0),
        "messages": int(db.query(func.count(Message.id)).scalar() or 0),
        "bots": int(db.query(func.count(TelegramBot.id)).scalar() or 0),
        "new_subscribers_period": sum(s["new_subscribers"] for s in series),
    }

    return {"days": days, "series": series, "top_bots": top_bots, "totals": totals}
