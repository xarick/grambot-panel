from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, BigInteger, Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.conversations.models import Conversation
    from app.modules.broadcast.models import BroadcastMessage


class TelegramBot(Base):
    __tablename__ = "telegram_bots"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    webhook_secret: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    webhook_base_url: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    welcome_message: Mapped[str] = mapped_column(String(4096), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)

    users: Mapped[list["TelegramUser"]] = relationship(back_populates="bot", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="bot", cascade="all, delete-orphan")
    broadcasts: Mapped[list["BroadcastMessage"]] = relationship(back_populates="bot")

    __table_args__ = (Index("ix_telegram_bots_token", "token"),)


class BotChat(Base):
    """A channel/group/supergroup the bot is a member or admin of."""

    __tablename__ = "bot_chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("telegram_bots.id", ondelete="CASCADE"), nullable=False)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="", nullable=False)  # group | supergroup | channel
    title: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    username: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    bot_status: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    description: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    member_count: Mapped[int | None] = mapped_column(nullable=True, default=None)
    admins: Mapped[list | None] = mapped_column(JSON, nullable=True, default=None)
    synced_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    added_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("bot_id", "chat_id", name="uq_bot_chats_bot_chat"),
        Index("ix_bot_chats_bot_id", "bot_id"),
    )


class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("telegram_bots.id", ondelete="CASCADE"), nullable=False)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), default="", nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)

    bot: Mapped["TelegramBot"] = relationship(back_populates="users")
    conversation: Mapped["Conversation"] = relationship(back_populates="user", uselist=False)

    __table_args__ = (
        UniqueConstraint("bot_id", "telegram_id", name="uq_telegram_users_bot_telegram"),
    )

    @property
    def full_name(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else f"User {self.telegram_id}"
