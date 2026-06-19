from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.automation import repository
from app.modules.automation.models import AutoReply
from app.modules.bots import repository as bot_repo

SUPPORTED_LANGUAGES = ("uz", "ru", "en")
DEFAULT_LANGUAGE = "uz"


def _clean_i18n(values: dict) -> dict:
    """Keep only supported languages, trimmed."""
    return {lang: (values.get(lang) or "").strip() for lang in SUPPORTED_LANGUAGES}


def _default_value(cleaned: dict) -> str:
    """The default-language variant, or the first non-empty one — mirrored into
    the legacy single-text column so old readers still work."""
    return cleaned.get(DEFAULT_LANGUAGE) or next((v for v in cleaned.values() if v), "")


def list_auto_replies(db: Session, bot_id: int) -> list[AutoReply]:
    return repository.get_by_bot(db, bot_id)


def create_auto_reply(db: Session, bot_id: int, keyword: str, responses: dict, match_mode: str) -> AutoReply:
    if not bot_repo.get_by_id(db, bot_id):
        raise NotFoundError("Bot not found")
    mode = match_mode if match_mode in ("contains", "exact") else "contains"
    cleaned = _clean_i18n(responses)
    return repository.create(db, bot_id, keyword, _default_value(cleaned), mode, response_i18n=cleaned)


def delete_auto_reply(db: Session, reply_id: int) -> None:
    row = repository.get_by_id(db, reply_id)
    if not row:
        raise NotFoundError("Auto-reply not found")
    repository.delete(db, row)


def set_welcome_message(db: Session, bot_id: int, welcome: dict):
    bot = bot_repo.get_by_id(db, bot_id)
    if not bot:
        raise NotFoundError("Bot not found")
    cleaned = _clean_i18n(welcome)
    return bot_repo.update(db, bot, welcome_i18n=cleaned, welcome_message=_default_value(cleaned))
