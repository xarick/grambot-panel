from sqlalchemy.orm import Session

from app.modules.broadcast.models import BroadcastMessage


def get_all(db: Session) -> list[BroadcastMessage]:
    return db.query(BroadcastMessage).order_by(BroadcastMessage.created_at.desc()).all()


def get_paginated(
    db: Session, limit: int, offset: int
) -> tuple[list[BroadcastMessage], int]:
    q = db.query(BroadcastMessage).order_by(BroadcastMessage.created_at.desc())
    total = q.count()
    items = q.limit(limit).offset(offset).all()
    return items, total


def get_by_id(db: Session, broadcast_id: int) -> BroadcastMessage | None:
    return db.query(BroadcastMessage).filter(BroadcastMessage.id == broadcast_id).first()


def create(db: Session, bot_id: int | None, text: str, created_by_id: int, **extra) -> BroadcastMessage:
    broadcast = BroadcastMessage(bot_id=bot_id, text=text, created_by_id=created_by_id, **extra)
    db.add(broadcast)
    db.commit()
    db.refresh(broadcast)
    return broadcast


def get_due_scheduled(db: Session, now) -> list[BroadcastMessage]:
    return (
        db.query(BroadcastMessage)
        .filter(BroadcastMessage.status == "scheduled", BroadcastMessage.scheduled_at <= now)
        .all()
    )


def claim_scheduled(db: Session, broadcast_id: int) -> bool:
    """Atomically move scheduled -> sending. Returns True only for the caller
    that won the row, so a broadcast can never be dispatched twice."""
    rows = (
        db.query(BroadcastMessage)
        .filter(BroadcastMessage.id == broadcast_id, BroadcastMessage.status == "scheduled")
        .update({BroadcastMessage.status: "sending"}, synchronize_session=False)
    )
    db.commit()
    return rows == 1


def cancel_scheduled(db: Session, broadcast_id: int) -> bool:
    """Atomically move scheduled -> canceled. Returns False if the scheduler
    already claimed the row, so a sending broadcast can't be canceled mid-flight."""
    rows = (
        db.query(BroadcastMessage)
        .filter(BroadcastMessage.id == broadcast_id, BroadcastMessage.status == "scheduled")
        .update({BroadcastMessage.status: "canceled"}, synchronize_session=False)
    )
    db.commit()
    return rows == 1


def cancel_all_scheduled_for_bot(db: Session, bot_id: int) -> int:
    """Cancel every scheduled broadcast tied to this bot. Called when the bot
    is being deleted so the SET NULL cascade can't leave orphaned schedules
    that fire against every user in the system."""
    rows = (
        db.query(BroadcastMessage)
        .filter(BroadcastMessage.bot_id == bot_id, BroadcastMessage.status == "scheduled")
        .update({BroadcastMessage.status: "canceled"}, synchronize_session=False)
    )
    db.commit()
    return rows


def update(db: Session, broadcast: BroadcastMessage, **kwargs) -> BroadcastMessage:
    for key, value in kwargs.items():
        setattr(broadcast, key, value)
    db.commit()
    db.refresh(broadcast)
    return broadcast


def delete(db: Session, broadcast: BroadcastMessage) -> None:
    db.delete(broadcast)
    db.commit()
