from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.bots.models import TelegramBot
    from app.modules.users.models import User


class BroadcastMessage(Base):
    __tablename__ = "broadcast_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[int | None] = mapped_column(
        ForeignKey("telegram_bots.id", ondelete="SET NULL"), nullable=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # 20 chars: longest current value is "canceled" (8); extra headroom
    # avoids a migration if we add states like "sending_paused" later.
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    media_type: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    media_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    buttons: Mapped[str] = mapped_column(Text, default="", nullable=False)
    segment_tag: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    total_recipients: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)

    bot: Mapped["TelegramBot | None"] = relationship(back_populates="broadcasts")
    created_by: Mapped["User | None"] = relationship(back_populates="broadcasts")

    __table_args__ = (
        # Composite index supports the scheduler's "due rows" query, which
        # filters on status and scheduled_at every tick.
        Index("ix_broadcast_messages_scheduled_due", "status", "scheduled_at"),
    )
