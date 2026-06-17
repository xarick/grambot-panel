from sqlalchemy.orm import Session

from app.core import config
from app.modules.settings import repository

WEBHOOK_BASE_URL_KEY = "webhook_base_url"


def get_webhook_base_url(db: Session) -> str:
    """Effective webhook base URL: DB-stored value, falling back to env config."""
    stored = repository.get(db, WEBHOOK_BASE_URL_KEY)
    if stored:
        return stored.rstrip("/")
    return (config.WEBHOOK_BASE_URL or "").rstrip("/")


def set_webhook_base_url(db: Session, url: str) -> str:
    url = (url or "").strip().rstrip("/")
    repository.set(db, WEBHOOK_BASE_URL_KEY, url)

    # Re-point every bot's webhook at the new domain.
    from app.modules.bots import service as bots_service

    bots_service.reregister_all_webhooks(db)
    return url
