"""
Configuration settings for the Interactive Barge Dashboard.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    KNOWLEDGE_BASE_DIR: Path = PROJECT_ROOT / "knowledge_base"
    MODELS_DIR: Path = PROJECT_ROOT / "models"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"

    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/barge_db"
    DB_ECHO: bool = False  # SQL query logging
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # Dashboard
    DASHBOARD_PORT: int = 8501
    DASHBOARD_TITLE: str = "Interactive Barge Dashboard"

    # External APIs (optional)
    USACE_LPMS_API_KEY: Optional[str] = None
    NOAA_API_KEY: Optional[str] = None
    EIA_API_KEY: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # Cache settings
    ROUTE_CACHE_TTL: int = 3600  # 1 hour
    ENABLE_CACHE: bool = True

    # ML Models
    MODEL_PATH: str = "models/"
    DELAY_PREDICTOR_MODEL: str = "delay_predictor_v1.pkl"

    # ChromaDB / RAG
    CHROMA_DB_PATH: str = "./chromadb"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Development
    DEBUG_MODE: bool = True
    ALLOW_ORIGIN: str = "*"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.MODELS_DIR.mkdir(exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


# Convenience exports
settings = get_settings()

# Data file paths (from plan specification)
DATA_FILES = {
    "waterway_networks": settings.DATA_DIR / "09_bts_waterway_networks" / "Waterway_Networks_7107995240912772581.csv",
    "waterway_nodes": settings.DATA_DIR / "10_bts_waterway_nodes" / "Waterway_Networks_7112991831811577565.csv",
    "locks": settings.DATA_DIR / "04_bts_locks" / "Locks_-3795028687405442582.csv",
    "docks": settings.DATA_DIR / "05_bts_navigation_fac" / "Docks_8605051818000540974.csv",
    "link_tonnages": settings.DATA_DIR / "03_bts_link_tons" / "Link_Tonnages_1612260770216529761.csv",
    "vessels": settings.DATA_DIR / "01.03_vessels" / "01_ships_register.csv",
}

# Knowledge base paths
KNOWLEDGE_BASE_FILES = {
    "processed_dir": settings.KNOWLEDGE_BASE_DIR / "processed",
    "index_file": settings.KNOWLEDGE_BASE_DIR / "processed" / "document_index.json",
}

# Cost constants (from knowledge base - BargeTariffCalculator)
COST_CONSTANTS = {
    "fuel_consumption_gallons_per_day": 100,
    "fuel_price_per_gallon_usd": 3.50,
    "crew_size": 8,
    "crew_cost_per_day_usd": 800,
    "average_speed_mph": 5.0,
    "lock_fee_usd": 50,  # Average lock passage fee
    "terminal_fee_usd": 750,  # Average terminal fee (400-1100 range)
    "safety_margin_depth_meters": 1.5,  # Vessel draft + 1.5m minimum depth
}

# Routing constraints
ROUTING_CONSTRAINTS = {
    "min_depth_safety_margin_m": 1.5,
    "max_lock_wait_time_hours": 24,
    "max_route_distance_miles": 5000,
}
