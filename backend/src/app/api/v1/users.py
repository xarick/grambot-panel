from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import require_superuser
from app.db.session import get_db
from app.modules.users.schemas import UserCreate, UserOut, UserUpdate
from app.modules.users.service import create, delete, get_all, update
from app.modules.users.models import User

router = APIRouter()


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_superuser)):
    return get_all(db)


@router.post("", response_model=UserOut)
def add_user(body: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_superuser)):
    return create(db, body.username, body.password, body.is_superuser)


@router.patch("/{user_id}", response_model=UserOut)
def edit_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db), _: User = Depends(require_superuser)):
    return update(db, user_id, body.username, body.password, body.is_superuser, body.is_active)


@router.delete("/{user_id}", status_code=204)
def remove_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_superuser)):
    delete(db, user_id)
