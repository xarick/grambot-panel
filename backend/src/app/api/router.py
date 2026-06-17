from fastapi import APIRouter

from app.api.v1 import (
    auth,
    automation,
    bots,
    broadcast,
    conversations,
    settings,
    stats,
    templates,
    users,
    webhook,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(bots.router, prefix="/bots", tags=["bots"])
api_router.include_router(conversations.router, tags=["conversations"])
api_router.include_router(broadcast.router, prefix="/broadcast", tags=["broadcast"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(automation.router, prefix="/automation", tags=["automation"])
api_router.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
