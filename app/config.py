"""Application configuration."""
import os
from typing import Optional


class Settings:
    """Application settings."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/data_visualizer"
    )

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
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


settings = Settings()
