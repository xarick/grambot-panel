import asyncio
import mimetypes
import os

import telegram

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.bots import repository as bot_repo
from app.modules.conversations import repository
from app.modules.conversations.models import Conversation, Message
from app.modules.conversations.schemas import ConversationListOut, ConversationOut, MessageListOut, MessageOut


def list_conversations(
    db: Session,
    bot_id: int,
    tag: str | None,
    search: str | None,
    limit: int,
    offset: int,
) -> ConversationListOut:
    items, total = repository.get_conversations(db, bot_id, tag, search, min(limit, 200), offset)
    conv_ids = [c.id for c in items]
    unread_map = repository.get_unread_counts(db, conv_ids) if conv_ids else {}

    out_items = [
        ConversationOut.model_validate(conv).model_copy(
            update={"unread_count": unread_map.get(conv.id, 0)}
        )
        for conv in items
    ]
    return ConversationListOut(items=out_items, total=total)


def get_conversation(db: Session, conv_id: int) -> Conversation:
    conv = repository.get_by_id(db, conv_id)
    if not conv:
        raise NotFoundError("Conversation not found")
    return conv


def update_conversation(db: Session, conv_id: int, is_open: bool | None, tag: str | None) -> Conversation:
    conv = get_conversation(db, conv_id)
    kwargs = {}
    if is_open is not None:
        kwargs["is_open"] = is_open
    if tag is not None:
        kwargs["tag"] = tag
    if kwargs:
        conv = repository.update(db, conv, **kwargs)
    return conv


def block_user(db: Session, conv_id: int, is_blocked: bool) -> Conversation:
    conv = get_conversation(db, conv_id)
    bot_repo.update_telegram_user(db, conv.user, is_blocked=is_blocked)
    return conv


def get_messages(
    db: Session,
    conv_id: int,
    after: int | None,
    before: int | None,
) -> MessageListOut | list[MessageOut]:
    get_conversation(db, conv_id)

    if after is not None:
        repository.mark_as_read(db, conv_id)
        msgs = repository.get_messages_after(db, conv_id, after)
        return [MessageOut.model_validate(m) for m in msgs]

    if before is not None:
        msgs = repository.get_messages_before(db, conv_id, before)
        return [MessageOut.model_validate(m) for m in msgs]

    msgs, has_more = repository.get_messages_last(db, conv_id)
    return MessageListOut(items=[MessageOut.model_validate(m) for m in msgs], has_more=has_more)


async def _send_message_async(token: str, chat_id: int, text: str) -> int:
    async with telegram.Bot(token=token) as bot:
        sent_msg = await bot.send_message(chat_id=chat_id, text=text)
        return sent_msg.message_id


async def _download_file_async(token: str, file_id: str) -> tuple[bytes, str]:
    async with telegram.Bot(token=token) as bot:
        file = await bot.get_file(file_id)
        data = await file.download_as_bytearray()
        return bytes(data), file.file_path or ""


def reply(db: Session, conv_id: int, text: str, sent_by_id: int) -> Message:
    conv = get_conversation(db, conv_id)
    bot_row = bot_repo.get_by_id(db, conv.bot_id)
    if not bot_row or not bot_row.is_active:
        raise ForbiddenError("Bot is not active")

    tg_user = conv.user
    try:
        tg_msg_id = asyncio.run(_send_message_async(bot_row.token, tg_user.telegram_id, text))
    except Exception as e:
        raise ForbiddenError(f"Failed to send message: {e}")

    msg = repository.create_message(
        db,
        conversation_id=conv_id,
        direction="outgoing",
        text=text,
        message_type="text",
        telegram_message_id=tg_msg_id,
        sent_by_id=sent_by_id,
    )
    repository.touch_conversation(db, conv)
    return msg


def get_file(db: Session, msg_id: int) -> tuple[bytes, str, str]:
    """Download a Telegram file server-side and return (content, filename,
    media_type). The bot token must never reach the client, so the file is
    proxied here instead of redirecting to the Telegram URL."""
    msg = repository.get_message_by_id(db, msg_id)
    if not msg or not msg.file_id:
        raise NotFoundError("File not found")

    bot_row = bot_repo.get_by_id(db, msg.conversation.bot_id)
    if not bot_row:
        raise NotFoundError("Bot not found")

    try:
        content, file_path = asyncio.run(_download_file_async(bot_row.token, msg.file_id))
    except Exception as e:
        raise ForbiddenError(f"Failed to get file: {e}")

    filename = msg.file_name or os.path.basename(file_path) or f"file-{msg_id}"
    media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return content, filename, media_type
