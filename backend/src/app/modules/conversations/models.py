from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.bots.models import TelegramBot, TelegramUser
    from app.modules.users.models import User


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("telegram_bots.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("telegram_users.id", ondelete="CASCADE"), nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)

    bot: Mapped["TelegramBot"] = relationship(back_populates="conversations")
    user: Mapped["TelegramUser"] = relationship(back_populates="conversation")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("bot_id", "user_id", name="uq_conversations_bot_user"),
        Index("ix_conversations_bot_id", "bot_id"),
        Index("ix_conversations_last_message_at", "last_message_at"),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), default="text", nullable=False)
    file_id: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    sent_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    sent_by: Mapped["User | None"] = relationship(back_populates="messages")

    __table_args__ = (Index("ix_messages_conversation_id", "conversation_id"),)
