from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_superuser
from app.db.session import get_db
from app.modules.settings.schemas import SettingsOut, SettingsUpdate
from app.modules.settings.service import get_webhook_base_url, set_webhook_base_url
from app.modules.users.models import User

router = APIRouter()


@router.get("", response_model=SettingsOut)
def read_settings(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return SettingsOut(webhook_base_url=get_webhook_base_url(db))


@router.put("", response_model=SettingsOut)
def update_settings(
    body: SettingsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    url = set_webhook_base_url(db, body.webhook_base_url)
    return SettingsOut(webhook_base_url=url)
