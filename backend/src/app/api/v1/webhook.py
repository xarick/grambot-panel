import hmac
import logging

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, UnauthorizedError
from app.db.session import get_db
from app.modules.bots import repository as bot_repo
from app.modules.telegram.handler import handle_update

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{token}/")
async def webhook(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    bot = bot_repo.get_by_token(db, token)
    if not bot or not bot.is_active:
        raise NotFoundError("Bot not found")

    if bot.webhook_secret:
        if not hmac.compare_digest(x_telegram_bot_api_secret_token or "", bot.webhook_secret):
            raise UnauthorizedError("Invalid webhook secret")

    data = await request.json()

    # Never let an application error bubble back to Telegram: a non-200 makes
    # Telegram retry the same update for hours, replaying side effects.
    try:
        handle_update(bot, data, db)
    except Exception:
        db.rollback()
        logger.exception("Failed to process update for bot %s", bot.id)

    return {"ok": True}
