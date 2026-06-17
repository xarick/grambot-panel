import json
import logging
import os
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.modules.broadcast import repository
from app.modules.broadcast.models import BroadcastMessage
from app.modules.broadcast.schemas import (
    BUTTON_TEXT_LIMIT,
    CAPTION_LIMIT,
    MAX_BUTTONS,
    TEXT_LIMIT,
)

logger = logging.getLogger(__name__)

MEDIA_BASE = os.path.realpath(os.path.join(os.getcwd(), "media", "broadcast"))
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def remove_media_file(media_path: str) -> None:
    """Best-effort removal of an uploaded media file. Guards against
    path-traversal by refusing anything that resolves outside MEDIA_BASE.
    Shared by the delete endpoint, the worker, and stuck-broadcast recovery."""
    if not media_path:
        return
    try:
        resolved = os.path.realpath(media_path)
        if resolved != MEDIA_BASE and not resolved.startswith(MEDIA_BASE + os.sep):
            return
        if os.path.exists(resolved):
            os.remove(resolved)
    except OSError as exc:
        logger.warning("Failed to remove media %s: %s", media_path, exc)


def _validate_button(text: str, url: str) -> None:
    if not text or not text.strip():
        raise AppError("Button text is required")
    if len(text) > BUTTON_TEXT_LIMIT:
        raise AppError(f"Button text must be at most {BUTTON_TEXT_LIMIT} characters")
    if not url or not _URL_RE.match(url.strip()):
        raise AppError("Button URL must start with http:// or https://")


def _validate_media_path(media_path: str) -> None:
    """Reject any path that does not resolve inside the upload directory,
    so a crafted media_path can't make the worker read arbitrary files."""
    resolved = os.path.realpath(media_path)
    if resolved != MEDIA_BASE and not resolved.startswith(MEDIA_BASE + os.sep):
        raise AppError("Invalid media path")


def list_broadcasts(db: Session, limit: int = 20, offset: int = 0) -> dict:
    items, total = repository.get_paginated(db, min(limit, 100), max(offset, 0))
    return {"items": items, "total": total}


def count_recipients(db: Session, bot_id: int, segment_tag: str = "") -> int:
    from app.modules.bots import repository as bot_repo

    return bot_repo.count_active_users_for_broadcast(db, bot_id, segment_tag or None)


def create_broadcast(
    db: Session,
    bot_id: int,
    text: str,
    created_by_id: int,
    scheduled_at: datetime | None = None,
    segment_tag: str = "",
    media_type: str = "",
    media_path: str = "",
    buttons: list | None = None,
) -> BroadcastMessage:
    from app.modules.bots import repository as bot_repo

    bot = bot_repo.get_by_id(db, bot_id)
    if not bot:
        raise NotFoundError("Bot not found")
    if not bot.is_active:
        raise AppError("Bot is not active")

    if media_path:
        _validate_media_path(media_path)

    text_stripped = (text or "").strip()
    if not text_stripped and not media_path:
        raise AppError("Either text or media is required")
    # Telegram refuses captions > 1024 chars; without media the limit is 4096.
    effective_limit = CAPTION_LIMIT if media_path else TEXT_LIMIT
    if len(text or "") > effective_limit:
        raise AppError(f"Text must be at most {effective_limit} characters")

    if buttons and len(buttons) > MAX_BUTTONS:
        raise AppError(f"At most {MAX_BUTTONS} buttons are allowed")
    for b in buttons or []:
        bt = b.text if hasattr(b, "text") else b.get("text", "")
        bu = b.url if hasattr(b, "url") else b.get("url", "")
        _validate_button(bt, bu)

    status = "draft"
    if scheduled_at is not None:
        # normalize to aware UTC
        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
        if scheduled_at <= datetime.now(timezone.utc):
            raise AppError("Scheduled time must be in the future")
        status = "scheduled"

    return repository.create(
        db,
        bot_id=bot_id,
        text=text,
        created_by_id=created_by_id,
        status=status,
        scheduled_at=scheduled_at,
        segment_tag=segment_tag or "",
        media_type=media_type or "",
        media_path=media_path or "",
        buttons=json.dumps([
            b.model_dump(mode="json") if hasattr(b, "model_dump") else b
            for b in (buttons or [])
        ]),
    )


def get_broadcast(db: Session, broadcast_id: int) -> BroadcastMessage:
    b = repository.get_by_id(db, broadcast_id)
    if not b:
        raise NotFoundError("Broadcast not found")
    return b


def cancel_broadcast(db: Session, broadcast_id: int) -> BroadcastMessage:
    b = repository.get_by_id(db, broadcast_id)
    if not b:
        raise NotFoundError("Broadcast not found")
    if b.status != "scheduled":
        raise AppError("Only scheduled broadcasts can be canceled")
    if not repository.cancel_scheduled(db, broadcast_id):
        raise AppError("Broadcast is no longer cancelable")
    db.refresh(b)
    return b


_DELETABLE_STATUSES = {"sent", "failed", "canceled"}


def delete_broadcast(db: Session, broadcast_id: int) -> None:
    b = repository.get_by_id(db, broadcast_id)
    if not b:
        raise NotFoundError("Broadcast not found")
    if b.status not in _DELETABLE_STATUSES:
        raise AppError("Only completed broadcasts can be deleted")
    remove_media_file(b.media_path)
    repository.delete(db, b)
