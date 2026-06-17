import asyncio
import threading

import telegram

from sqlalchemy.orm import Session

from app.modules.bots import repository as bot_repo
from app.modules.bots.models import TelegramBot
from app.modules.conversations import repository as conv_repo

ALLOWED_DOCUMENT_MIME_PREFIXES = ("image/", "application/pdf", "text/")
ALLOWED_DOCUMENT_EXTENSIONS = (".pdf", ".txt", ".doc", ".docx", ".zip", ".png", ".jpg", ".jpeg", ".gif")
REJECTED_TYPES_MSG = "Sorry, I can only receive text, photos, stickers, and documents."


_CHAT_TYPES = ("group", "supergroup", "channel")
_PRESENT_STATUSES = ("member", "administrator", "creator")


def _record_chat_membership(bot_row: TelegramBot, update, db: Session) -> None:
    """Track channels/groups the bot is added to / removed from."""
    cmu = update.my_chat_member
    if not cmu or not cmu.chat or cmu.chat.type not in _CHAT_TYPES:
        return
    status = cmu.new_chat_member.status if cmu.new_chat_member else "left"
    if status in _PRESENT_STATUSES:
        bot_repo.upsert_bot_chat(
            db,
            bot_id=bot_row.id,
            chat_id=cmu.chat.id,
            chat_type=cmu.chat.type,
            title=cmu.chat.title or "",
            username=cmu.chat.username or "",
            status=status,
        )
    else:  # left | kicked | restricted
        bot_repo.remove_bot_chat(db, bot_row.id, cmu.chat.id)


def handle_update(bot_row: TelegramBot, data: dict, db: Session) -> None:
    update = telegram.Update.de_json(data, None)

    if update.my_chat_member:
        _record_chat_membership(bot_row, update, db)
        return

    message = update.message or update.edited_message
    if not message:
        return

    # Keep group/channel traffic out of the private-chat inbox; also refresh
    # chat metadata if the bot sees activity in a known group/channel.
    if message.chat and message.chat.type in _CHAT_TYPES:
        bot_repo.upsert_bot_chat(
            db,
            bot_id=bot_row.id,
            chat_id=message.chat.id,
            chat_type=message.chat.type,
            title=message.chat.title or "",
            username=message.chat.username or "",
            status=None,  # don't downgrade a known admin status on plain activity
        )
        return

    tg_from = message.from_user
    if not tg_from:
        return

    tg_user = bot_repo.get_telegram_user(db, bot_row.id, tg_from.id)
    if not tg_user:
        tg_user = bot_repo.create_telegram_user(
            db,
            bot_id=bot_row.id,
            telegram_id=tg_from.id,
            username=tg_from.username or "",
            first_name=tg_from.first_name or "",
            last_name=tg_from.last_name or "",
            language_code=tg_from.language_code or "",
        )
        if bot_row.welcome_message:
            _send_text(bot_row.token, tg_from.id, bot_row.welcome_message)
    else:
        bot_repo.update_telegram_user(
            db,
            tg_user,
            username=tg_from.username or "",
            first_name=tg_from.first_name or "",
            last_name=tg_from.last_name or "",
        )

    if tg_user.is_blocked:
        return

    conv, _ = conv_repo.get_or_create(db, bot_id=bot_row.id, user_id=tg_user.id)

    msg_type = "other"
    text = message.text or message.caption or ""
    file_id = ""
    file_name = ""

    if message.text:
        msg_type = "text"
    elif message.photo:
        msg_type = "photo"
        file_id = message.photo[-1].file_id
    elif message.sticker:
        msg_type = "sticker"
        file_id = message.sticker.file_id
    elif message.document:
        doc = message.document
        mime = doc.mime_type or ""
        fname = doc.file_name or ""
        ext = "." + fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
        if any(mime.startswith(p) for p in ALLOWED_DOCUMENT_MIME_PREFIXES) or ext in ALLOWED_DOCUMENT_EXTENSIONS:
            msg_type = "document"
            file_id = doc.file_id
            file_name = fname
        else:
            _send_rejection(bot_row.token, tg_from.id)
            return
    else:
        _send_rejection(bot_row.token, tg_from.id)
        return

    conv_repo.create_message(
        db,
        conversation_id=conv.id,
        direction="incoming",
        text=text,
        message_type=msg_type,
        file_id=file_id,
        file_name=file_name,
        telegram_message_id=message.message_id,
    )
    conv_repo.touch_conversation(db, conv)

    if msg_type == "text" and text:
        from app.modules.automation import repository as automation_repo

        rule = automation_repo.find_match(db, bot_row.id, text)
        if rule:
            _send_text(bot_row.token, tg_from.id, rule.response)
            conv_repo.create_message(
                db,
                conversation_id=conv.id,
                direction="outgoing",
                text=rule.response,
                message_type="text",
            )
            conv_repo.touch_conversation(db, conv)


def _send_text(token: str, chat_id: int, text: str) -> None:
    async def _send():
        async with telegram.Bot(token=token) as bot:
            await bot.send_message(chat_id=chat_id, text=text)

    def _run():
        try:
            asyncio.run(_send())
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


def _send_rejection(token: str, chat_id: int) -> None:
    _send_text(token, chat_id, REJECTED_TYPES_MSG)
