from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_superuser
from app.db.session import get_db
from app.modules.automation.schemas import AutoReplyCreate, AutoReplyOut, WelcomeUpdate
from app.modules.automation.service import (
    create_auto_reply,
    delete_auto_reply,
    list_auto_replies,
    set_welcome_message,
)
from app.modules.bots.service import get_bot_or_404
from app.modules.users.models import User

router = APIRouter()


@router.get("/auto-replies", response_model=list[AutoReplyOut])
def list_replies(
    bot_id: int = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list_auto_replies(db, bot_id)


@router.post("/auto-replies", response_model=AutoReplyOut)
def add_reply(
    body: AutoReplyCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    return create_auto_reply(db, body.bot_id, body.keyword, body.responses, body.match_mode)


@router.delete("/auto-replies/{reply_id}", status_code=204)
def remove_reply(
    reply_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    delete_auto_reply(db, reply_id)


@router.get("/welcome")
def get_welcome(
    bot_id: int = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    bot = get_bot_or_404(db, bot_id)
    src = bot.welcome_i18n or {"uz": bot.welcome_message}
    welcome = {lang: src.get(lang, "") for lang in ("uz", "ru", "en")}
    return {"bot_id": bot_id, "welcome": welcome}


@router.put("/welcome")
def put_welcome(
    bot_id: int = Query(...),
    body: WelcomeUpdate = ...,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    bot = set_welcome_message(db, bot_id, body.welcome)
    return {"bot_id": bot_id, "welcome": bot.welcome_i18n}
