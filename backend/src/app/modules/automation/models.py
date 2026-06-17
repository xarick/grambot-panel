from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AutoReply(Base):
    __tablename__ = "auto_replies"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[int] = mapped_column(
        ForeignKey("telegram_bots.id", ondelete="CASCADE"), nullable=False
    )
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    match_mode: Mapped[str] = mapped_column(String(10), default="contains", nullable=False)  # contains | exact
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (Index("ix_auto_replies_bot_id", "bot_id"),)
