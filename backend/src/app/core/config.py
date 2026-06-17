import logging

from decouple import config

logger = logging.getLogger(__name__)

_INSECURE_SECRET = "dev-secret-key"

SECRET_KEY: str = config("SECRET_KEY", default=_INSECURE_SECRET)
ALGORITHM: str = config("ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=1440, cast=int)

DATABASE_URL: str = config("DATABASE_URL", default="postgresql://postgres:postgres@localhost:5432/tgpanel")

WEBHOOK_BASE_URL: str = config("WEBHOOK_BASE_URL", default="")
FRONTEND_URL: str = config("FRONTEND_URL", default="http://localhost:5173").rstrip("/")

DEBUG: bool = config("DEBUG", default=True, cast=bool)

ADMIN_USERNAME: str = config("ADMIN_USERNAME", default="")
ADMIN_PASSWORD: str = config("ADMIN_PASSWORD", default="")

ADMIN_LOGIN_PATH: str = config("ADMIN_LOGIN_PATH", default="/manage/login")

if SECRET_KEY == _INSECURE_SECRET:
    if not DEBUG:
        raise RuntimeError(
            "SECRET_KEY is not set. Set a long random SECRET_KEY in the "
            "environment before running with DEBUG=False."
        )
    logger.warning(
        "Using the built-in insecure SECRET_KEY. Set SECRET_KEY in your .env "
        "before deploying."
    )
