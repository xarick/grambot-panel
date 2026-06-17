import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_superuser
from app.db.session import get_db
from app.modules.bots import repository as bot_repo
from app.modules.bots.schemas import BotChatOut, BotCreate, BotOut, BotUpdate, ChatLiveInfo
from app.modules.bots.service import (
    create_bot,
    delete_bot,
    get_bot_or_404,
    get_chat_stored_info,
    list_bot_chats,
    list_bots,
    refresh_chat_info,
    update_bot,
)
from app.modules.users.models import User

router = APIRouter()


@router.get("", response_model=list[BotOut])
def get_bots(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list_bots(db)


@router.post("", response_model=BotOut)
def add_bot(body: BotCreate, db: Session = Depends(get_db), _: User = Depends(require_superuser)):
    return create_bot(db, body.name, body.token)


@router.patch("/{bot_id}", response_model=BotOut)
def edit_bot(bot_id: int, body: BotUpdate, db: Session = Depends(get_db), _: User = Depends(require_superuser)):
    return update_bot(db, bot_id, body.name, body.is_active, body.webhook_base_url)


@router.get("/{bot_id}/users.csv")
def export_users_csv(bot_id: int, db: Session = Depends(get_db), _: User = Depends(require_superuser)):
    bot = get_bot_or_404(db, bot_id)
    users = bot_repo.get_users_by_bot(db, bot_id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["telegram_id", "username", "first_name", "last_name", "language", "blocked", "joined_at"]
    )
    for u in users:
        writer.writerow([
            u.telegram_id,
            u.username,
            u.first_name,
            u.last_name,
            u.language_code,
            "yes" if u.is_blocked else "no",
            u.joined_at.isoformat() if u.joined_at else "",
        ])
    buf.seek(0)

    filename = f"subscribers_{bot.username or bot.id}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{bot_id}/chats", response_model=list[BotChatOut])
def bot_chats(bot_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list_bot_chats(db, bot_id)


@router.get("/{bot_id}/chats/{chat_row_id}/info", response_model=ChatLiveInfo)
def bot_chat_info(
    bot_id: int,
    chat_row_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_chat_stored_info(db, bot_id, chat_row_id)


@router.post("/{bot_id}/chats/{chat_row_id}/refresh", response_model=ChatLiveInfo)
def bot_chat_refresh(
    bot_id: int,
    chat_row_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return refresh_chat_info(db, bot_id, chat_row_id)


@router.delete("/{bot_id}", status_code=204)
def remove_bot(bot_id: int, db: Session = Depends(get_db), _: User = Depends(require_superuser)):
    delete_bot(db, bot_id)
