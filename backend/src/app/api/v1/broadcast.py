import os
import secrets
import threading

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.exceptions import AppError
from app.db.session import get_db
from app.modules.broadcast.schemas import (
    BroadcastCreate,
    BroadcastListOut,
    BroadcastOut,
    MediaUploadOut,
    RecipientCountOut,
)
from app.modules.broadcast.service import (
    cancel_broadcast,
    count_recipients,
    create_broadcast,
    delete_broadcast,
    get_broadcast,
    list_broadcasts,
)
from app.modules.users.models import User
from app.workers.tasks import send_broadcast_task

router = APIRouter()

MEDIA_DIR = os.path.join(os.getcwd(), "media", "broadcast")
MAX_MEDIA_BYTES = 50 * 1024 * 1024  # 50 MB
_EXT_TYPE = {
    ".jpg": "photo", ".jpeg": "photo", ".png": "photo", ".gif": "photo", ".webp": "photo",
    ".mp4": "video", ".mov": "video", ".avi": "video",
}


@router.get("", response_model=BroadcastListOut)
def get_broadcasts(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list_broadcasts(db, limit=limit, offset=offset)


@router.get("/recipients", response_model=RecipientCountOut)
def recipients(
    bot_id: int = Query(...),
    segment_tag: str = Query(default=""),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return RecipientCountOut(bot_id=bot_id, count=count_recipients(db, bot_id, segment_tag))


@router.post("/media", response_model=MediaUploadOut)
def upload_media(file: UploadFile = File(...), _: User = Depends(get_current_user)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    media_type = _EXT_TYPE.get(ext, "document")

    os.makedirs(MEDIA_DIR, exist_ok=True)
    safe_name = f"{secrets.token_hex(8)}{ext}"
    path = os.path.join(MEDIA_DIR, safe_name)

    size = 0
    with open(path, "wb") as out:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_MEDIA_BYTES:
                out.close()
                os.remove(path)
                raise AppError("File too large (max 50 MB)")
            out.write(chunk)

    return MediaUploadOut(media_type=media_type, media_path=path)


@router.post("", response_model=BroadcastOut)
def create(body: BroadcastCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    broadcast = create_broadcast(
        db,
        body.bot_id,
        body.text,
        user.id,
        scheduled_at=body.scheduled_at,
        segment_tag=body.segment_tag,
        media_type=body.media_type,
        media_path=body.media_path,
        buttons=body.buttons,
    )
    # Scheduled broadcasts are picked up by the scheduler; send the rest now.
    if broadcast.status != "scheduled":
        threading.Thread(target=send_broadcast_task, args=(broadcast.id,), daemon=True).start()
    return broadcast


@router.get("/{broadcast_id}", response_model=BroadcastOut)
def get_status(broadcast_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return get_broadcast(db, broadcast_id)


@router.post("/{broadcast_id}/cancel", response_model=BroadcastOut)
def cancel(broadcast_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return cancel_broadcast(db, broadcast_id)


@router.delete("/{broadcast_id}", status_code=204)
def delete(broadcast_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    delete_broadcast(db, broadcast_id)
    return None
