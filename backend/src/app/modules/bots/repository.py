from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.bots.models import BotChat, TelegramBot, TelegramUser
from app.modules.conversations.models import Conversation, Message


def get_all(db: Session) -> list[TelegramBot]:
    return db.query(TelegramBot).order_by(TelegramBot.created_at).all()


def get_by_id(db: Session, bot_id: int) -> TelegramBot | None:
    return db.query(TelegramBot).filter(TelegramBot.id == bot_id).first()


def get_by_token(db: Session, token: str) -> TelegramBot | None:
    return db.query(TelegramBot).filter(TelegramBot.token == token).first()


def create(db: Session, name: str, token: str, username: str, webhook_secret: str) -> TelegramBot:
    bot = TelegramBot(name=name, token=token, username=username, webhook_secret=webhook_secret)
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot


def update(db: Session, bot: TelegramBot, **kwargs) -> TelegramBot:
    for key, value in kwargs.items():
        setattr(bot, key, value)
    db.commit()
    db.refresh(bot)
    return bot


def delete(db: Session, bot: TelegramBot) -> None:
    db.delete(bot)
    db.commit()


def get_stats_batch(db: Session, bot_ids: list[int]) -> dict:
    user_counts = (
        db.query(TelegramUser.bot_id, func.count(TelegramUser.id))
        .filter(TelegramUser.bot_id.in_(bot_ids))
        .group_by(TelegramUser.bot_id)
        .all()
    )
    open_conv_counts = (
        db.query(Conversation.bot_id, func.count(Conversation.id))
        .filter(Conversation.bot_id.in_(bot_ids), Conversation.is_open == True)  # noqa: E712
        .group_by(Conversation.bot_id)
        .all()
    )
    unread_counts = (
        db.query(Conversation.bot_id, func.count(Message.id))
        .join(Message, Message.conversation_id == Conversation.id)
        .filter(
            Conversation.bot_id.in_(bot_ids),
            Message.direction == "incoming",
            Message.is_read == False,  # noqa: E712
        )
        .group_by(Conversation.bot_id)
        .all()
    )

    return {
        "user_counts": dict(user_counts),
        "open_conv_counts": dict(open_conv_counts),
        "unread_counts": dict(unread_counts),
    }


def get_telegram_user(db: Session, bot_id: int, telegram_id: int) -> TelegramUser | None:
    return (
        db.query(TelegramUser)
        .filter(TelegramUser.bot_id == bot_id, TelegramUser.telegram_id == telegram_id)
        .first()
    )


def create_telegram_user(
    db: Session,
    bot_id: int,
    telegram_id: int,
    username: str,
    first_name: str,
    last_name: str,
    language_code: str,
) -> TelegramUser:
    tg_user = TelegramUser(
        bot_id=bot_id,
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        language_code=language_code,
    )
    db.add(tg_user)
    try:
        db.commit()
    except IntegrityError:
        # A concurrent update created the same user first.
        db.rollback()
        return get_telegram_user(db, bot_id, telegram_id)
    db.refresh(tg_user)
    return tg_user


def update_telegram_user(db: Session, tg_user: TelegramUser, **kwargs) -> TelegramUser:
    for key, value in kwargs.items():
        setattr(tg_user, key, value)
    db.commit()
    db.refresh(tg_user)
    return tg_user


def _broadcast_query(db: Session, bot_id: int | None, segment_tag: str | None):
    q = db.query(TelegramUser).filter(TelegramUser.is_blocked == False)  # noqa: E712
    if bot_id is not None:
        q = q.filter(TelegramUser.bot_id == bot_id)
    if segment_tag:
        q = q.join(Conversation, Conversation.user_id == TelegramUser.id).filter(
            Conversation.tag == segment_tag
        )
    return q


def get_active_users_for_broadcast(
    db: Session, bot_id: int | None, segment_tag: str | None = None
) -> list[TelegramUser]:
    return _broadcast_query(db, bot_id, segment_tag).all()


def get_bot_chats(db: Session, bot_id: int) -> list[BotChat]:
    return (
        db.query(BotChat)
        .filter(BotChat.bot_id == bot_id)
        .order_by(BotChat.title)
        .all()
    )


def get_bot_chat(db: Session, chat_row_id: int) -> BotChat | None:
    return db.query(BotChat).filter(BotChat.id == chat_row_id).first()


def upsert_bot_chat(
    db: Session,
    bot_id: int,
    chat_id: int,
    chat_type: str,
    title: str,
    username: str,
    status: str | None = None,
) -> BotChat:
    """Upsert chat metadata. status=None keeps the existing status (used for
    plain message activity, which doesn't tell us the bot's membership status)."""
    row = (
        db.query(BotChat)
        .filter(BotChat.bot_id == bot_id, BotChat.chat_id == chat_id)
        .first()
    )
    if row:
        row.type = chat_type
        row.title = title
        row.username = username
        if status is not None:
            row.bot_status = status
    else:
        row = BotChat(
            bot_id=bot_id,
            chat_id=chat_id,
            type=chat_type,
            title=title,
            username=username,
            bot_status=status or "member",
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def save_chat_snapshot(db: Session, row: BotChat, **fields) -> BotChat:
    """Persist freshly fetched live info onto a bot_chats row."""
    for key, value in fields.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


def remove_bot_chat(db: Session, bot_id: int, chat_id: int) -> None:
    db.query(BotChat).filter(BotChat.bot_id == bot_id, BotChat.chat_id == chat_id).delete()
    db.commit()


def get_users_by_bot(db: Session, bot_id: int) -> list[TelegramUser]:
    return (
        db.query(TelegramUser)
        .filter(TelegramUser.bot_id == bot_id)
        .order_by(TelegramUser.joined_at)
        .all()
    )


def count_active_users_for_broadcast(
    db: Session, bot_id: int, segment_tag: str | None = None
) -> int:
    return _broadcast_query(db, bot_id, segment_tag).count()
