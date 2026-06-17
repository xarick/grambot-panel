import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone

import telegram

from app.db.session import SessionLocal
from app.modules.bots import repository as bot_repo
from app.modules.broadcast import repository as broadcast_repo

logger = logging.getLogger(__name__)

BATCH_SIZE = 25
BATCH_SLEEP = 1.0
MAX_FLOOD_WAITS = 5          # give up on a recipient after this many FloodWaits
MAX_TRANSIENT_RETRIES = 2    # network/timeout retries per recipient
FLOOD_WAIT_BUFFER = 1.0      # extra seconds added to Telegram's retry_after


def _build_markup(b) -> "telegram.InlineKeyboardMarkup | None":
    try:
        rows = json.loads(b.buttons or "[]")
    except (ValueError, TypeError):
        return None
    buttons = [
        [telegram.InlineKeyboardButton(text=r["text"], url=r["url"])]
        for r in rows
        if r.get("text") and r.get("url")
    ]
    return telegram.InlineKeyboardMarkup(buttons) if buttons else None


def _cleanup_media(b) -> None:
    """Free the uploaded media file once the broadcast reaches a terminal
    state, so the upload dir doesn't grow unboundedly. Wraps the shared
    remove_media_file helper, which performs the path-traversal guard."""
    from app.modules.broadcast.service import remove_media_file

    remove_media_file(b.media_path or "")


def _load_media(b) -> "tuple[str, bytes] | None":
    """Read the media file once so it isn't re-opened for every recipient.
    The path is re-validated here as defense-in-depth against arbitrary
    file reads, even though create_broadcast already checks it."""
    from app.modules.broadcast.service import MEDIA_BASE

    mt = b.media_type or ""
    if not (mt and b.media_path):
        return None
    resolved = os.path.realpath(b.media_path)
    if resolved != MEDIA_BASE and not resolved.startswith(MEDIA_BASE + os.sep):
        logger.warning("Skipping out-of-bounds media path: %s", b.media_path)
        return None
    if not os.path.exists(resolved):
        return None
    with open(resolved, "rb") as f:
        return mt, f.read()


def _send_payload(bot: telegram.Bot, chat_id: int, b, markup, media):
    """Return the coroutine for sending this broadcast to one chat."""
    if media:
        mt, data = media
        caption = b.text or None
        if mt == "photo":
            return bot.send_photo(chat_id=chat_id, photo=data, caption=caption, reply_markup=markup)
        if mt == "video":
            return bot.send_video(chat_id=chat_id, video=data, caption=caption, reply_markup=markup)
        return bot.send_document(chat_id=chat_id, document=data, caption=caption, reply_markup=markup)
    return bot.send_message(chat_id=chat_id, text=b.text, reply_markup=markup)


def _send_one(loop, bot: telegram.Bot, chat_id: int, b, markup, media) -> str:
    """Send one broadcast message, honoring Telegram FloodWait. Returns 'sent' | 'forbidden' | 'failed'."""
    flood_waits = 0
    transient = 0
    while True:
        try:
            loop.run_until_complete(_send_payload(bot, chat_id, b, markup, media))
            return "sent"
        except telegram.error.RetryAfter as exc:
            flood_waits += 1
            if flood_waits > MAX_FLOOD_WAITS:
                logger.warning("Giving up on %s after %d FloodWaits", chat_id, flood_waits)
                return "failed"
            wait = float(getattr(exc, "retry_after", 1)) + FLOOD_WAIT_BUFFER
            logger.info("FloodWait: sleeping %.1fs before retrying %s", wait, chat_id)
            time.sleep(wait)
        except telegram.error.Forbidden:
            return "forbidden"
        except telegram.error.BadRequest as exc:
            logger.warning("BadRequest for %s: %s", chat_id, exc)
            return "failed"
        except (telegram.error.TimedOut, telegram.error.NetworkError) as exc:
            transient += 1
            if transient > MAX_TRANSIENT_RETRIES:
                logger.warning("Network failure for %s: %s", chat_id, exc)
                return "failed"
            time.sleep(2.0)
        except Exception as exc:
            logger.warning("Failed to send to %s: %s", chat_id, exc)
            return "failed"


def recover_stuck_broadcasts(db) -> int:
    """Mark broadcasts left mid-flight by a crashed/restarted process as failed."""
    stuck = [
        b for b in broadcast_repo.get_all(db)
        if b.status in ("sending", "draft")
    ]
    for b in stuck:
        broadcast_repo.update(
            db, b, status="failed", finished_at=datetime.now(timezone.utc)
        )
        # Stuck broadcasts won't be retried, so the cached media file is
        # unreachable now — release the disk space.
        _cleanup_media(b)
    if stuck:
        logger.info("Recovered %d stuck broadcast(s)", len(stuck))
    return len(stuck)


def send_broadcast_task(broadcast_id: int) -> None:
    db = SessionLocal()
    try:
        _run(db, broadcast_id)
    except Exception as exc:
        logger.exception("Broadcast %s failed: %s", broadcast_id, exc)
        b = broadcast_repo.get_by_id(db, broadcast_id)
        if b:
            broadcast_repo.update(db, b, status="failed")
            _cleanup_media(b)
    finally:
        db.close()


def _run(db, broadcast_id: int) -> None:
    b = broadcast_repo.get_by_id(db, broadcast_id)
    if not b:
        return

    # Defense in depth: a deleted bot leaves bot_id=NULL (SET NULL FK).
    # Without this guard, get_active_users_for_broadcast would return EVERY
    # user in the system and we'd send the broadcast cross-bot.
    if b.bot_id is None:
        broadcast_repo.update(
            db, b, status="failed", finished_at=datetime.now(timezone.utc)
        )
        _cleanup_media(b)
        return

    broadcast_repo.update(db, b, status="sending", started_at=datetime.now(timezone.utc))

    users = bot_repo.get_active_users_for_broadcast(db, b.bot_id, b.segment_tag or None)
    broadcast_repo.update(db, b, total_recipients=len(users))
    markup = _build_markup(b)
    media = _load_media(b)

    if not users:
        broadcast_repo.update(db, b, status="sent", finished_at=datetime.now(timezone.utc))
        _cleanup_media(b)
        return

    bot_tokens: dict[int, str] = {}
    for tg_user in users:
        if tg_user.bot_id not in bot_tokens:
            bot_row = bot_repo.get_by_id(db, tg_user.bot_id)
            if bot_row:
                bot_tokens[tg_user.bot_id] = bot_row.token

    sent = 0
    failed = 0

    loop = asyncio.new_event_loop()
    bot_map: dict[int, telegram.Bot] = {}
    try:
        for bot_id, token in bot_tokens.items():
            bot = telegram.Bot(token=token)
            loop.run_until_complete(bot.initialize())
            bot_map[bot_id] = bot

        for i, tg_user in enumerate(users):
            bot = bot_map.get(tg_user.bot_id)
            if not bot:
                failed += 1
                continue

            result = _send_one(loop, bot, tg_user.telegram_id, b, markup, media)
            if result == "sent":
                sent += 1
            elif result == "forbidden":
                bot_repo.update_telegram_user(db, tg_user, is_blocked=True)
                failed += 1
            else:
                failed += 1

            if (i + 1) % BATCH_SIZE == 0:
                broadcast_repo.update(db, b, sent_count=sent, failed_count=failed)
                time.sleep(BATCH_SLEEP)
    finally:
        for bot in bot_map.values():
            try:
                loop.run_until_complete(bot.shutdown())
            except Exception:
                pass
        loop.close()

    broadcast_repo.update(
        db,
        b,
        status="sent",
        sent_count=sent,
        failed_count=failed,
        finished_at=datetime.now(timezone.utc),
    )
    _cleanup_media(b)


SCHEDULER_INTERVAL = 30  # seconds


def _scheduler_loop() -> None:
    import threading

    while True:
        try:
            db = SessionLocal()
            try:
                due = broadcast_repo.get_due_scheduled(db, datetime.now(timezone.utc))
                for b in due:
                    if broadcast_repo.claim_scheduled(db, b.id):
                        threading.Thread(
                            target=send_broadcast_task, args=(b.id,), daemon=True
                        ).start()
            finally:
                db.close()
        except Exception as exc:  # never let the scheduler die
            logger.exception("Scheduler tick failed: %s", exc)
        time.sleep(SCHEDULER_INTERVAL)


def start_scheduler() -> None:
    import threading

    threading.Thread(target=_scheduler_loop, daemon=True, name="broadcast-scheduler").start()
    logger.info("Broadcast scheduler started")
