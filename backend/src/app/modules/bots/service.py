import asyncio
import logging
import secrets
from datetime import datetime, timezone

import telegram

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.modules.bots import repository
from app.modules.bots.models import TelegramBot
from app.modules.bots.schemas import BotOut
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


async def _get_me_async(token: str) -> str:
    async with telegram.Bot(token=token) as bot:
        me = await bot.get_me()
        return me.username or ""


async def _set_webhook_async(token: str, url: str, secret: str) -> None:
    async with telegram.Bot(token=token) as bot:
        await bot.set_webhook(url=url, secret_token=secret)


async def _delete_webhook_async(token: str) -> None:
    async with telegram.Bot(token=token) as bot:
        await bot.delete_webhook()


def _get_bot_info(token: str) -> str:
    try:
        return asyncio.run(_get_me_async(token))
    except telegram.error.InvalidToken:
        raise AppError("Invalid bot token")
    except Exception as e:
        raise AppError(f"Telegram API error: {e}")


def _set_webhook(token: str, url: str, secret: str) -> None:
    try:
        asyncio.run(_set_webhook_async(token, url, secret))
    except Exception as exc:
        logger.warning("Failed to set webhook: %s", exc)


def _delete_webhook(token: str) -> None:
    try:
        asyncio.run(_delete_webhook_async(token))
    except Exception as exc:
        logger.warning("Failed to delete webhook: %s", exc)


def list_bots(db: Session) -> list[BotOut]:
    bots = repository.get_all(db)
    if not bots:
        return []

    bot_ids = [b.id for b in bots]
    stats = repository.get_stats_batch(db, bot_ids)

    return [
        BotOut.model_validate(bot).model_copy(update={
            "webhook_url": _resolve_base_url(db, bot.webhook_base_url),
            "user_count": stats["user_counts"].get(bot.id, 0),
            "open_conversation_count": stats["open_conv_counts"].get(bot.id, 0),
            "unread_count": stats["unread_counts"].get(bot.id, 0),
        })
        for bot in bots
    ]


def _global_base_url(db: Session) -> str:
    from app.modules.settings.service import get_webhook_base_url

    return get_webhook_base_url(db)


def _resolve_base_url(db: Session, bot_override: str) -> str:
    """Per-bot URL wins; otherwise fall back to the global/env default."""
    override = (bot_override or "").strip().rstrip("/")
    return override or _global_base_url(db)


def _apply_webhook(db: Session, bot: TelegramBot) -> None:
    base = _resolve_base_url(db, bot.webhook_base_url)
    if base and bot.is_active:
        _set_webhook(bot.token, f"{base}/api/v1/webhook/{bot.token}/", bot.webhook_secret)
    else:
        _delete_webhook(bot.token)


def reregister_all_webhooks(db: Session) -> None:
    """Re-point every bot's webhook at its effective base URL (or remove it)."""
    for bot in repository.get_all(db):
        _apply_webhook(db, bot)


def create_bot(db: Session, name: str, token: str) -> TelegramBot:
    if repository.get_by_token(db, token):
        raise ConflictError("A bot with this token already exists")

    username = _get_bot_info(token)
    webhook_secret = secrets.token_urlsafe(48)[:64]
    bot = repository.create(db, name=name, token=token, username=username, webhook_secret=webhook_secret)

    _apply_webhook(db, bot)
    return bot


def update_bot(
    db: Session,
    bot_id: int,
    name: str | None,
    is_active: bool | None,
    webhook_base_url: str | None = None,
) -> TelegramBot:
    bot = repository.get_by_id(db, bot_id)
    if not bot:
        raise NotFoundError("Bot not found")

    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if is_active is not None:
        kwargs["is_active"] = is_active
    if webhook_base_url is not None:
        kwargs["webhook_base_url"] = webhook_base_url.strip().rstrip("/")

    webhook_dirty = (
        ("is_active" in kwargs and kwargs["is_active"] != bot.is_active)
        or ("webhook_base_url" in kwargs and kwargs["webhook_base_url"] != bot.webhook_base_url)
    )

    if kwargs:
        bot = repository.update(db, bot, **kwargs)

    if webhook_dirty:
        _apply_webhook(db, bot)

    return bot


def delete_bot(db: Session, bot_id: int) -> None:
    bot = repository.get_by_id(db, bot_id)
    if not bot:
        raise NotFoundError("Bot not found")
    # Cancel any pending scheduled broadcasts BEFORE deleting the bot:
    # once bot_id becomes NULL (SET NULL FK), the scheduler would otherwise
    # fire them with a null bot filter and broadcast to every user.
    from app.modules.broadcast import repository as broadcast_repo
    broadcast_repo.cancel_all_scheduled_for_bot(db, bot_id)
    _delete_webhook(bot.token)
    repository.delete(db, bot)


def get_bot_or_404(db: Session, bot_id: int) -> TelegramBot:
    bot = repository.get_by_id(db, bot_id)
    if not bot:
        raise NotFoundError("Bot not found")
    return bot


def list_bot_chats(db: Session, bot_id: int):
    get_bot_or_404(db, bot_id)
    return repository.get_bot_chats(db, bot_id)


async def _chat_info_async(token: str, chat_id: int) -> dict:
    async with telegram.Bot(token=token) as bot:
        chat = await bot.get_chat(chat_id)
        try:
            count = await bot.get_chat_member_count(chat_id)
        except Exception:
            count = None
        admins = []
        try:
            for m in await bot.get_chat_administrators(chat_id):
                u = m.user
                admins.append({
                    "id": u.id,
                    "username": u.username or "",
                    "name": (f"{u.first_name or ''} {u.last_name or ''}").strip() or str(u.id),
                    "status": m.status,
                    "is_bot": bool(u.is_bot),
                })
        except Exception:
            pass
        return {
            "title": chat.title or "",
            "type": chat.type,
            "username": chat.username or "",
            "description": getattr(chat, "description", "") or "",
            "member_count": count,
            "admins": admins,
        }


def _chat_to_dict(chat) -> dict:
    """Build the ChatLiveInfo payload from the cached bot_chats row."""
    return {
        "chat_id": chat.chat_id,
        "title": chat.title or "",
        "type": chat.type or "",
        "username": chat.username or "",
        "description": chat.description or "",
        "member_count": chat.member_count,
        "bot_status": chat.bot_status,
        "admins": chat.admins or [],
        "synced_at": chat.synced_at,
    }


def _get_chat_or_404(db: Session, bot_id: int, chat_row_id: int):
    chat = repository.get_bot_chat(db, chat_row_id)
    if not chat or chat.bot_id != bot_id:
        raise NotFoundError("Chat not found")
    return chat


def get_chat_stored_info(db: Session, bot_id: int, chat_row_id: int) -> dict:
    """Return the last cached snapshot from the database (no Telegram call)."""
    get_bot_or_404(db, bot_id)
    chat = _get_chat_or_404(db, bot_id, chat_row_id)
    return _chat_to_dict(chat)


def refresh_chat_info(db: Session, bot_id: int, chat_row_id: int) -> dict:
    """Fetch fresh data from Telegram, persist it to the DB, and return it."""
    bot = get_bot_or_404(db, bot_id)
    chat = _get_chat_or_404(db, bot_id, chat_row_id)
    try:
        info = asyncio.run(_chat_info_async(bot.token, chat.chat_id))
    except telegram.error.Forbidden:
        raise AppError("Bot is no longer a member of this chat")
    except Exception as e:
        raise AppError(f"Telegram API error: {e}")
    repository.save_chat_snapshot(
        db,
        chat,
        title=info["title"],
        username=info["username"],
        type=info["type"],
        description=info["description"],
        member_count=info["member_count"],
        admins=info["admins"],
        synced_at=datetime.now(timezone.utc),
    )
    return _chat_to_dict(chat)
