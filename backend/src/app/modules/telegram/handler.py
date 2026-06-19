import asyncio
import threading

import telegram

from sqlalchemy.orm import Session

from app.modules.bots import repository as bot_repo
from app.modules.bots.models import TelegramBot
from app.modules.conversations import repository as conv_repo

SUPPORTED_LANGUAGES = ("uz", "ru", "en")
DEFAULT_LANGUAGE = "uz"

# Shown before the user has chosen a language, so it stays trilingual — anyone
# understands it on first contact.
_CHOOSE_LANGUAGE_PROMPT = "🌐 Tilni tanlang · Выберите язык · Choose your language"

_STRINGS = {
    "language_set": {
        "uz": "✅ Til o'zbekchaga o'rnatildi.",
        "ru": "✅ Язык переключён на русский.",
        "en": "✅ Language set to English.",
    },
    "rejected_types": {
        "uz": "Kechirasiz, men faqat matn va rasm qabul qila olaman.",
        "ru": "Извините, я принимаю только текст и фото.",
        "en": "Sorry, I can only receive text and photos.",
    },
}


def _t(key: str, language: str) -> str:
    """Pick a system string for the user's chosen language (falling back to the
    default for unknown/empty codes)."""
    lang = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    return _STRINGS[key][lang]


def _localized(i18n: dict | None, fallback: str, language: str) -> str:
    """Pick admin-authored text (welcome / auto-reply) for the user's language.
    Falls back to the default-language variant, then to the legacy single-text
    column."""
    if i18n:
        lang = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        return i18n.get(lang) or i18n.get(DEFAULT_LANGUAGE) or fallback
    return fallback


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

    if update.callback_query:
        _handle_language_callback(bot_row, update.callback_query, db)
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
    is_new_user = tg_user is None
    if is_new_user:
        tg_user = bot_repo.create_telegram_user(
            db,
            bot_id=bot_row.id,
            telegram_id=tg_from.id,
            username=tg_from.username or "",
            first_name=tg_from.first_name or "",
            last_name=tg_from.last_name or "",
            language_code=tg_from.language_code or "",
        )
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

    text = message.text or message.caption or ""
    command = text.split(maxsplit=1)[0].lower() if text.startswith("/") else ""

    # /start and /language let the user pick (or later change) their language.
    if command in ("/start", "/language"):
        conv_repo.create_message(
            db,
            conversation_id=conv.id,
            direction="incoming",
            text=text,
            message_type="text",
            telegram_message_id=message.message_id,
        )
        conv_repo.touch_conversation(db, conv)
        _send_language_picker(bot_row.token, tg_from.id)
        return

    # A brand-new user who skipped /start still gets the welcome here; for the
    # /start flow the welcome is sent once the language has been chosen.
    if is_new_user:
        welcome = _localized(bot_row.welcome_i18n, bot_row.welcome_message, tg_user.language_code)
        if welcome:
            _send_text(bot_row.token, tg_from.id, welcome)

    msg_type = "other"
    file_id = ""
    file_name = ""

    if message.text:
        msg_type = "text"
    elif message.photo:
        # A "photo" is re-encoded to a clean JPEG by Telegram's servers, so the
        # original bytes (and any embedded payload) never reach us. Images sent
        # "as a file" arrive as message.document instead and are rejected below.
        msg_type = "photo"
        file_id = message.photo[-1].file_id
    else:
        # Only text and photos are accepted. Documents, stickers, video, audio,
        # voice, etc. are rejected and never stored, so untrusted binaries never
        # reach the panel.
        _send_rejection(bot_row.token, tg_from.id, tg_user.language_code)
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
            response = _localized(rule.response_i18n, rule.response, tg_user.language_code)
            _send_text(bot_row.token, tg_from.id, response)
            conv_repo.create_message(
                db,
                conversation_id=conv.id,
                direction="outgoing",
                text=response,
                message_type="text",
            )
            conv_repo.touch_conversation(db, conv)


def _run_async(coro_factory) -> None:
    """Fire-and-forget a Telegram coroutine on a daemon thread so the webhook
    handler never blocks on outbound network I/O."""

    def _run():
        try:
            asyncio.run(coro_factory())
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


def _send_text(token: str, chat_id: int, text: str) -> None:
    async def _send():
        async with telegram.Bot(token=token) as bot:
            await bot.send_message(chat_id=chat_id, text=text)

    _run_async(_send)


def _send_language_picker(token: str, chat_id: int) -> None:
    keyboard = telegram.InlineKeyboardMarkup(
        [
            [
                telegram.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang:uz"),
                telegram.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
                telegram.InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
            ]
        ]
    )

    async def _send():
        async with telegram.Bot(token=token) as bot:
            await bot.send_message(chat_id=chat_id, text=_CHOOSE_LANGUAGE_PROMPT, reply_markup=keyboard)

    _run_async(_send)


def _answer_callback(token: str, callback_query_id: str) -> None:
    async def _send():
        async with telegram.Bot(token=token) as bot:
            await bot.answer_callback_query(callback_query_id)

    _run_async(_send)


def _handle_language_callback(bot_row: TelegramBot, callback_query, db: Session) -> None:
    """Store the language the user tapped, then confirm + (re)send the welcome."""
    data = callback_query.data or ""
    tg_from = callback_query.from_user
    lang = data.split(":", 1)[1] if data.startswith("lang:") else ""

    if not tg_from or lang not in SUPPORTED_LANGUAGES:
        _answer_callback(bot_row.token, callback_query.id)
        return

    tg_user = bot_repo.get_telegram_user(db, bot_row.id, tg_from.id)
    if tg_user:
        bot_repo.update_telegram_user(db, tg_user, language_code=lang)

    _answer_callback(bot_row.token, callback_query.id)
    _send_text(bot_row.token, tg_from.id, _t("language_set", lang))
    welcome = _localized(bot_row.welcome_i18n, bot_row.welcome_message, lang)
    if welcome:
        _send_text(bot_row.token, tg_from.id, welcome)


def _send_rejection(token: str, chat_id: int, language: str) -> None:
    _send_text(token, chat_id, _t("rejected_types", language))
