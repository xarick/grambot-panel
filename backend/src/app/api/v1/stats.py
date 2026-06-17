from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.modules.stats.schemas import StatsOut
from app.modules.stats.service import get_stats
from app.modules.users.models import User

router = APIRouter()


@router.get("", response_model=StatsOut)
def read_stats(
    days: int = Query(default=14, ge=1, le=90),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_stats(db, days)
