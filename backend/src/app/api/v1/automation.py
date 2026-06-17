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
    return create_auto_reply(db, body.bot_id, body.keyword, body.response, body.match_mode)


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
    return {"bot_id": bot_id, "welcome_message": bot.welcome_message}


@router.put("/welcome")
def put_welcome(
    bot_id: int = Query(...),
    body: WelcomeUpdate = ...,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    bot = set_welcome_message(db, bot_id, body.welcome_message)
    return {"bot_id": bot_id, "welcome_message": bot.welcome_message}
