from app.db.base import Base  # noqa: F401

# Import all models so Alembic discovers them through Base.metadata
from app.modules.users.models import User  # noqa: F401
from app.modules.bots.models import BotChat, TelegramBot, TelegramUser  # noqa: F401
from app.modules.conversations.models import Conversation, Message  # noqa: F401
from app.modules.broadcast.models import BroadcastMessage  # noqa: F401
from app.modules.templates.models import MessageTemplate  # noqa: F401
from app.modules.settings.models import AppSetting  # noqa: F401
from app.modules.automation.models import AutoReply  # noqa: F401
