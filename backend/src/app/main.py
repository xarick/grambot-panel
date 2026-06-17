import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core import config
from app.core.exceptions import AppError
from app.db.session import SessionLocal
from app.modules.users import service as user_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _ensure_superuser() -> None:
    if not config.ADMIN_USERNAME or not config.ADMIN_PASSWORD:
        return
    db = SessionLocal()
    try:
        user = user_service.ensure_superuser(db, config.ADMIN_USERNAME, config.ADMIN_PASSWORD)
        if user:
            logger.info("Superuser '%s' created automatically", config.ADMIN_USERNAME)
    finally:
        db.close()


def _recover_stuck_broadcasts() -> None:
    from app.workers.tasks import recover_stuck_broadcasts

    db = SessionLocal()
    try:
        recover_stuck_broadcasts(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.workers.tasks import start_scheduler

    _ensure_superuser()
    _recover_stuck_broadcasts()
    start_scheduler()
    yield


app = FastAPI(title="tg-panel", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(api_router, prefix="/api/v1")


@app.get("/healthz")
def healthz():
    """Liveness probe for the container healthcheck (no DB hit)."""
    return {"status": "ok"}
