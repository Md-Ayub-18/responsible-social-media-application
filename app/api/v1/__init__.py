from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    bot_detection,
    focus_modes,
    guardian,
    interests,
    moderation,
    posts,
    profiles,
    reports,
    stitch,
    uploads,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(interests.router)
api_router.include_router(users.router)
api_router.include_router(profiles.router)
api_router.include_router(focus_modes.router)
api_router.include_router(posts.router)
api_router.include_router(uploads.router)
api_router.include_router(stitch.router)
api_router.include_router(moderation.router)
api_router.include_router(reports.router)
api_router.include_router(guardian.router)
api_router.include_router(bot_detection.router)
api_router.include_router(admin.router)
