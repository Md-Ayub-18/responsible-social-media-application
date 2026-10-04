import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_router
from app.config import settings
from app.db.session import AsyncSessionLocal
from app.services.interest_service import InterestService

os.environ["TRANSFORMERS_VERBOSITY"] = "error"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME} in {settings.APP_ENV} mode")
    # Seed interests on first run
    async with AsyncSessionLocal() as db:
        count = await InterestService(db).seed_if_empty()
        if count:
            print(f"🌱 Seeded {count} interests")
    yield
    print("🛑 Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="An interest-focused social platform with user-controlled feeds.",
    lifespan=lifespan,
)

# Serve uploaded/stitched media
media_root = Path(settings.MEDIA_ROOT).resolve()
media_root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_root)), name="media")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/", tags=["root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}
