"""Application configuration."""

import os
from typing import Optional


class Settings:
    """Application settings."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/data_visualizer"
    )

    # Server
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Application
    APP_NAME: str = "Data Visualizer"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "PostgreSQL-backed data visualization and exploration platform"

    # API
    API_PREFIX: str = "/api"
    DOCS_URL: str = "/docs"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000

    # Optional Redis cache (#26)
    REDIS_URL: str | None = __import__("os").getenv("REDIS_URL") or None
    REDIS_TTL_SECONDS: int = int(__import__("os").getenv("REDIS_TTL_SECONDS", "30"))

    # Optional auth (#27)
    UI_AUTH_TOKEN: str | None = __import__("os").getenv("UI_AUTH_TOKEN") or None
    AUTH_DISABLED: bool = __import__("os").getenv("AUTH_DISABLED", "false").lower() == "true"

    # Freshness (#31)
    FRESHNESS_WEBHOOK: str | None = __import__("os").getenv("FRESHNESS_WEBHOOK") or None



settings = Settings()
