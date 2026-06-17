"""initial schema

Consolidated production schema. All tables, indexes, and constraints are
created in a single migration — earlier incremental migrations were squashed
because the database is recreated from scratch before launch.

Revision ID: 0001
Revises:
Create Date: 2026-05-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------------------------------------------------------- users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(150), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )

    # -------------------------------------------------------- telegram_bots
    op.create_table(
        "telegram_bots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("token", sa.String(100), unique=True, nullable=False),
        sa.Column("username", sa.String(100), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("webhook_secret", sa.String(255), nullable=False, server_default=""),
        sa.Column("webhook_base_url", sa.String(255), nullable=False, server_default=""),
        sa.Column("welcome_message", sa.String(4096), nullable=False, server_default=""),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_telegram_bots_token", "telegram_bots", ["token"])

    # ------------------------------------------------------- telegram_users
    op.create_table(
        "telegram_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "bot_id",
            sa.Integer(),
            sa.ForeignKey("telegram_bots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(100), nullable=False, server_default=""),
        sa.Column("first_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("last_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("language_code", sa.String(10), nullable=False, server_default=""),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("joined_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint("bot_id", "telegram_id", name="uq_telegram_users_bot_telegram"),
    )

    # ------------------------------------------------------------ bot_chats
    op.create_table(
        "bot_chats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "bot_id",
            sa.Integer(),
            sa.ForeignKey("telegram_bots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False, server_default=""),
        sa.Column("title", sa.String(255), nullable=False, server_default=""),
        sa.Column("username", sa.String(100), nullable=False, server_default=""),
        sa.Column("bot_status", sa.String(20), nullable=False, server_default="member"),
        sa.Column("description", sa.String(1024), nullable=False, server_default=""),
        sa.Column("member_count", sa.Integer(), nullable=True),
        sa.Column("admins", sa.JSON(), nullable=True),
        sa.Column("synced_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("added_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint("bot_id", "chat_id", name="uq_bot_chats_bot_chat"),
    )
    op.create_index("ix_bot_chats_bot_id", "bot_chats", ["bot_id"])

    # -------------------------------------------------------- conversations
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "bot_id",
            sa.Integer(),
            sa.ForeignKey("telegram_bots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("telegram_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("tag", sa.String(100), nullable=True),
        sa.Column("last_message_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint("bot_id", "user_id", name="uq_conversations_bot_user"),
    )
    op.create_index("ix_conversations_bot_id", "conversations", ["bot_id"])
    op.create_index("ix_conversations_last_message_at", "conversations", ["last_message_at"])

    # ------------------------------------------------------------- messages
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.Column("message_type", sa.String(20), nullable=False, server_default="text"),
        sa.Column("file_id", sa.String(255), nullable=False, server_default=""),
        sa.Column("file_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "sent_by_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    # Partial index: speeds up "unread inbox" queries by only indexing the
    # incoming, unread rows — keeps the index small on PostgreSQL.
    op.create_index(
        "ix_messages_unread_incoming",
        "messages",
        ["is_read"],
        postgresql_where=sa.text("direction = 'incoming' AND is_read = false"),
    )

    # -------------------------------------------------- broadcast_messages
    # status values: draft | scheduled | sending | sent | failed | canceled
    op.create_table(
        "broadcast_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "bot_id",
            sa.Integer(),
            sa.ForeignKey("telegram_bots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("media_type", sa.String(20), nullable=False, server_default=""),
        sa.Column("media_path", sa.String(500), nullable=False, server_default=""),
        sa.Column("buttons", sa.Text(), nullable=False, server_default=""),
        sa.Column("segment_tag", sa.String(100), nullable=False, server_default=""),
        sa.Column("total_recipients", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_by_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    # Helps the scheduler tick look up due rows without scanning the table.
    op.create_index(
        "ix_broadcast_messages_scheduled_due",
        "broadcast_messages",
        ["status", "scheduled_at"],
    )

    # ---------------------------------------------------- message_templates
    op.create_table(
        "message_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_by_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )

    # --------------------------------------------------------- app_settings
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
    )

    # ---------------------------------------------------------- auto_replies
    op.create_table(
        "auto_replies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "bot_id",
            sa.Integer(),
            sa.ForeignKey("telegram_bots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("keyword", sa.String(255), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("match_mode", sa.String(10), nullable=False, server_default="contains"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_auto_replies_bot_id", "auto_replies", ["bot_id"])


def downgrade() -> None:
    # Drop in reverse dependency order so child tables go before parents.
    op.drop_index("ix_auto_replies_bot_id", table_name="auto_replies")
    op.drop_table("auto_replies")

    op.drop_table("app_settings")

    op.drop_table("message_templates")

    op.drop_index("ix_broadcast_messages_scheduled_due", table_name="broadcast_messages")
    op.drop_table("broadcast_messages")

    op.drop_index("ix_messages_unread_incoming", table_name="messages")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_conversations_last_message_at", table_name="conversations")
    op.drop_index("ix_conversations_bot_id", table_name="conversations")
    op.drop_table("conversations")

    op.drop_index("ix_bot_chats_bot_id", table_name="bot_chats")
    op.drop_table("bot_chats")

    op.drop_table("telegram_users")

    op.drop_index("ix_telegram_bots_token", table_name="telegram_bots")
    op.drop_table("telegram_bots")

    op.drop_table("users")
