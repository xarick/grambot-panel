from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.broadcast.models import BroadcastMessage
    from app.modules.templates.models import MessageTemplate
    from app.modules.conversations.models import Message


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)

    broadcasts: Mapped[list["BroadcastMessage"]] = relationship(back_populates="created_by")
    templates: Mapped[list["MessageTemplate"]] = relationship(back_populates="created_by")
    messages: Mapped[list["Message"]] = relationship(back_populates="sent_by")
