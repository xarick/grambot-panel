import io

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
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
    reply_photo,
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


@router.post("/conversations/{conv_id}/reply-photo", response_model=MessageOut)
async def send_reply_photo(
    conv_id: int,
    file: UploadFile = File(...),
    caption: str = Form(default=""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await file.read()
    # reply_photo() uses asyncio.run() internally, which can't run inside this
    # async request's event loop — offload it to a worker thread (same as how
    # FastAPI runs the sync text-reply endpoint).
    msg = await run_in_threadpool(reply_photo, db, conv_id, content, caption, user.id)
    return MessageOut.model_validate(msg)


@router.get("/messages/{msg_id}/file")
def download_file(msg_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    content, filename, media_type = get_file(db, msg_id)
    # Strip characters that could break out of the header; nosniff stops the
    # browser from re-interpreting the bytes as executable HTML/JS.
    safe_name = filename.translate({ord(c): None for c in '"\\\r\n'})
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{safe_name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
