from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, contains_eager, joinedload

from app.modules.bots.models import TelegramUser
from app.modules.conversations.models import Conversation, Message


def get_conversations(
    db: Session,
    bot_id: int,
    tag: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Conversation], int]:
    pattern = f"%{search}%" if search else None

    q = (
        db.query(Conversation)
        .join(TelegramUser, Conversation.user_id == TelegramUser.id)
        .options(contains_eager(Conversation.user))
        .filter(Conversation.bot_id == bot_id)
    )
    if tag:
        q = q.filter(Conversation.tag == tag)
    if pattern:
        q = q.filter(
            TelegramUser.first_name.ilike(pattern)
            | TelegramUser.last_name.ilike(pattern)
            | TelegramUser.username.ilike(pattern)
        )

    total_q = db.query(func.count(Conversation.id)).filter(Conversation.bot_id == bot_id)
    if tag:
        total_q = total_q.filter(Conversation.tag == tag)
    if pattern:
        total_q = total_q.join(TelegramUser, Conversation.user_id == TelegramUser.id).filter(
            TelegramUser.first_name.ilike(pattern)
            | TelegramUser.last_name.ilike(pattern)
            | TelegramUser.username.ilike(pattern)
        )
    total = total_q.scalar()

    items = q.order_by(Conversation.last_message_at.desc().nullslast()).offset(offset).limit(limit).all()
    return items, total


def get_by_id(db: Session, conv_id: int) -> Conversation | None:
    return (
        db.query(Conversation)
        .options(joinedload(Conversation.user))
        .filter(Conversation.id == conv_id)
        .first()
    )


def get_or_create(db: Session, bot_id: int, user_id: int) -> tuple[Conversation, bool]:
    conv = (
        db.query(Conversation)
        .filter(Conversation.bot_id == bot_id, Conversation.user_id == user_id)
        .first()
    )
    if conv:
        return conv, False
    conv = Conversation(bot_id=bot_id, user_id=user_id)
    db.add(conv)
    try:
        db.commit()
    except IntegrityError:
        # A concurrent update created the conversation first.
        db.rollback()
        conv = (
            db.query(Conversation)
            .filter(Conversation.bot_id == bot_id, Conversation.user_id == user_id)
            .first()
        )
        return conv, False
    db.refresh(conv)
    return conv, True


def update(db: Session, conv: Conversation, **kwargs) -> Conversation:
    for key, value in kwargs.items():
        setattr(conv, key, value)
    db.commit()
    db.refresh(conv)
    return conv


def get_messages_last(db: Session, conv_id: int, limit: int = 50) -> tuple[list[Message], bool]:
    q = db.query(Message).filter(Message.conversation_id == conv_id)
    total = q.count()
    items = q.order_by(Message.id.desc()).limit(limit).all()
    items = list(reversed(items))
    return items, total > limit


def get_messages_after(db: Session, conv_id: int, after: int) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conv_id, Message.id > after)
        .order_by(Message.id)
        .all()
    )


def get_messages_before(db: Session, conv_id: int, before: int) -> list[Message]:
    items = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id, Message.id < before)
        .order_by(Message.id.desc())
        .limit(50)
        .all()
    )
    return list(reversed(items))


def mark_as_read(db: Session, conv_id: int) -> None:
    db.query(Message).filter(
        Message.conversation_id == conv_id,
        Message.direction == "incoming",
        Message.is_read == False,  # noqa: E712
    ).update({"is_read": True})
    db.commit()


def create_message(
    db: Session,
    conversation_id: int,
    direction: str,
    text: str = "",
    message_type: str = "text",
    file_id: str = "",
    file_name: str = "",
    telegram_message_id: int | None = None,
    sent_by_id: int | None = None,
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        direction=direction,
        text=text,
        message_type=message_type,
        file_id=file_id,
        file_name=file_name,
        telegram_message_id=telegram_message_id,
        sent_by_id=sent_by_id,
        is_read=direction == "outgoing",
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_unread_counts(db: Session, conv_ids: list[int]) -> dict[int, int]:
    rows = (
        db.query(Message.conversation_id, func.count(Message.id))
        .filter(
            Message.conversation_id.in_(conv_ids),
            Message.direction == "incoming",
            Message.is_read == False,  # noqa: E712
        )
        .group_by(Message.conversation_id)
        .all()
    )
    return dict(rows)


def get_message_by_id(db: Session, msg_id: int) -> Message | None:
    return db.query(Message).options(joinedload(Message.conversation)).filter(Message.id == msg_id).first()


def touch_conversation(db: Session, conv: Conversation) -> None:
    conv.last_message_at = datetime.now(timezone.utc)
    db.commit()
