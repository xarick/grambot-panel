from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.users.models import User


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_all(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at).all()


def superuser_exists(db: Session) -> bool:
    count = db.query(func.count(User.id)).filter(User.is_superuser == True).scalar()  # noqa: E712
    return count > 0


def create(db: Session, username: str, hashed_password: str, is_superuser: bool = False) -> User:
    user = User(username=username, hashed_password=hashed_password, is_superuser=is_superuser)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update(db: Session, user: User, **kwargs) -> User:
    for key, value in kwargs.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def delete(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
