import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.modules.conversations.schemas import (
    BlockUserRequest,
    ConversationListOut,
    ConversationOut,
    ConversationUpdate,
    MessageListOut,
    MessageOut,
    ReplyRequest,
)
from app.modules.conversations.service import (
    block_user,
    get_conversation,
    get_file,
    get_messages,
    list_conversations,
    reply,
    update_conversation,
)
from app.modules.users.models import User

router = APIRouter()


@router.get("/bots/{bot_id}/conversations", response_model=ConversationListOut)
def get_conversations(
    bot_id: int,
    tag: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list_conversations(db, bot_id, tag, search, limit, offset)


@router.get("/conversations/{conv_id}", response_model=ConversationOut)
def get_conv(conv_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    conv = get_conversation(db, conv_id)
    return ConversationOut.model_validate(conv)


@router.patch("/conversations/{conv_id}", response_model=ConversationOut)
def patch_conv(
    conv_id: int,
    body: ConversationUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    conv = update_conversation(db, conv_id, body.is_open, body.tag)
    return ConversationOut.model_validate(conv)


@router.patch("/conversations/{conv_id}/block")
def patch_block(
    conv_id: int,
    body: BlockUserRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    block_user(db, conv_id, body.is_blocked)
    return {"ok": True}


@router.get("/conversations/{conv_id}/messages")
def get_msgs(
    conv_id: int,
    after: int | None = Query(default=None),
    before: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_messages(db, conv_id, after, before)


@router.post("/conversations/{conv_id}/reply", response_model=MessageOut)
def send_reply(
    conv_id: int,
    body: ReplyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    msg = reply(db, conv_id, body.text, user.id)
    return MessageOut.model_validate(msg)


@router.get("/messages/{msg_id}/file")
def download_file(msg_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    content, filename, media_type = get_file(db, msg_id)
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
