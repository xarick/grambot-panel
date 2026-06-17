from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.users import repository as user_repo
from app.modules.users.models import User


def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not access_token:
        raise UnauthorizedError("Not authenticated")
    username = decode_access_token(access_token)
    if not username:
        raise UnauthorizedError("Invalid or expired token")
    user = user_repo.get_by_username(db, username)
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user


def require_superuser(user: User = Depends(get_current_user)) -> User:
    if not user.is_superuser:
        raise ForbiddenError("Superuser access required")
    return user
