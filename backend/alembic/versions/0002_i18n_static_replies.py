"""per-language welcome and auto-reply text

Adds JSON columns holding {"uz": ..., "ru": ..., "en": ...} variants so the bot
can answer each user in their chosen language. The original single-text columns
are kept as the default-language value and fallback.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("telegram_bots", sa.Column("welcome_i18n", sa.JSON(), nullable=True))
    op.add_column("auto_replies", sa.Column("response_i18n", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("auto_replies", "response_i18n")
    op.drop_column("telegram_bots", "welcome_i18n")
