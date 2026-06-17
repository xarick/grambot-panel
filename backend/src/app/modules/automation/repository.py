from sqlalchemy.orm import Session

from app.modules.automation.models import AutoReply


def get_by_bot(db: Session, bot_id: int) -> list[AutoReply]:
    return (
        db.query(AutoReply)
        .filter(AutoReply.bot_id == bot_id)
        .order_by(AutoReply.created_at)
        .all()
    )


def get_by_id(db: Session, reply_id: int) -> AutoReply | None:
    return db.query(AutoReply).filter(AutoReply.id == reply_id).first()


def create(db: Session, bot_id: int, keyword: str, response: str, match_mode: str) -> AutoReply:
    row = AutoReply(bot_id=bot_id, keyword=keyword, response=response, match_mode=match_mode)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete(db: Session, row: AutoReply) -> None:
    db.delete(row)
    db.commit()


def find_match(db: Session, bot_id: int, text: str) -> AutoReply | None:
    if not text:
        return None
    lowered = text.strip().lower()
    for rule in get_by_bot(db, bot_id):
        kw = rule.keyword.strip().lower()
        if not kw:
            continue
        if rule.match_mode == "exact":
            if lowered == kw:
                return rule
        elif kw in lowered:
            return rule
    return None
