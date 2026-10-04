from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # App
    APP_NAME: str = "Interest Social Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "dev-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # Database
    # DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/interest_social"
    # DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/interest_social"
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
        # Media
    MEDIA_ROOT: str = "./media"
    MEDIA_UPLOADS_DIR: str = "./media/uploads"
    MEDIA_STITCHED_DIR: str = "./media/stitched"
    MAX_UPLOAD_MB: int = 50
    MEDIA_POSTS_DIR: str = "./media/posts"
    MAX_POST_MEDIA_MB: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

