from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.modules.users import repository
from app.modules.users.models import User


def authenticate(db: Session, username: str, password: str) -> User:
    user = repository.get_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Invalid credentials")
    if not user.is_active:
        raise UnauthorizedError("Invalid credentials")
    return user


def get_all(db: Session) -> list[User]:
    return repository.get_all(db)


def create(db: Session, username: str, password: str, is_superuser: bool = False) -> User:
    if repository.get_by_username(db, username):
        raise ConflictError(f"Username '{username}' is already taken")
    return repository.create(db, username, hash_password(password), is_superuser)


def update(
    db: Session,
    user_id: int,
    username: str | None = None,
    password: str | None = None,
    is_superuser: bool | None = None,
    is_active: bool | None = None,
) -> User:
    user = repository.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("User not found")

    kwargs = {}
    if username is not None and username != user.username:
        if repository.get_by_username(db, username):
            raise ConflictError(f"Username '{username}' is already taken")
        kwargs["username"] = username
    if password:
        kwargs["hashed_password"] = hash_password(password)
    if is_superuser is not None:
        kwargs["is_superuser"] = is_superuser
    if is_active is not None:
        kwargs["is_active"] = is_active

    if kwargs:
        user = repository.update(db, user, **kwargs)
    return user


def update_profile(
    db: Session,
    user: User,
    username: str | None = None,
    current_password: str | None = None,
    new_password: str | None = None,
) -> User:
    kwargs = {}

    if username is not None and username != user.username:
        if repository.get_by_username(db, username):
            raise ConflictError(f"Username '{username}' is already taken")
        kwargs["username"] = username

    if new_password:
        if not current_password or not verify_password(current_password, user.hashed_password):
            raise UnauthorizedError("Current password is incorrect")
        kwargs["hashed_password"] = hash_password(new_password)

    if kwargs:
        user = repository.update(db, user, **kwargs)
    return user


def delete(db: Session, user_id: int) -> None:
    user = repository.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("User not found")
    repository.delete(db, user)


def ensure_superuser(db: Session, username: str, password: str) -> User | None:
    if repository.superuser_exists(db):
        return None
    return repository.create(db, username, hash_password(password), is_superuser=True)
