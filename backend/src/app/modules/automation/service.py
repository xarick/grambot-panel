from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.automation import repository
from app.modules.automation.models import AutoReply
from app.modules.bots import repository as bot_repo


def list_auto_replies(db: Session, bot_id: int) -> list[AutoReply]:
    return repository.get_by_bot(db, bot_id)


def create_auto_reply(db: Session, bot_id: int, keyword: str, response: str, match_mode: str) -> AutoReply:
    if not bot_repo.get_by_id(db, bot_id):
        raise NotFoundError("Bot not found")
    mode = match_mode if match_mode in ("contains", "exact") else "contains"
    return repository.create(db, bot_id, keyword, response, mode)


def delete_auto_reply(db: Session, reply_id: int) -> None:
    row = repository.get_by_id(db, reply_id)
    if not row:
        raise NotFoundError("Auto-reply not found")
    repository.delete(db, row)


def set_welcome_message(db: Session, bot_id: int, message: str):
    bot = bot_repo.get_by_id(db, bot_id)
    if not bot:
        raise NotFoundError("Bot not found")
    return bot_repo.update(db, bot, welcome_message=message)
