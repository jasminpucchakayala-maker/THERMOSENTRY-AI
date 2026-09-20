import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    APP_NAME: str = "THERMOSENTRY AI"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # NASA FIRMS API settings
    FIRMS_API_KEY: str = ""
    FIRMS_BASE_URL: str = "https://firms.modaps.eosdis.nasa.gov/api/"
    FIRMS_DEFAULT_SOURCE: str = "VIIRS_SNPP_NRT"
    FIRMS_DEFAULT_DAYS: int = 1
    FIRMS_DEFAULT_COUNTRY: str = "IND"
    FIRMS_TIMEOUT_SECONDS: float = 15.0

    # Persistence analysis settings
    PERSISTENCE_DISTANCE_THRESHOLD_KM: float = 1.0
    PERSISTENCE_TIME_WINDOW_DAYS: int = 10

    # OpenStreetMap Overpass settings
    OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
    OSM_SEARCH_RADIUS_KM: float = 5.0
    OSM_TIMEOUT_SECONDS: float = 6.0

    # Risk weights are configurable, but unavailable factors are never scored.
    RISK_WEIGHT_THERMAL_INTENSITY: float = 0.45
    RISK_WEIGHT_PERSISTENCE: float = 0.20
    RISK_WEIGHT_INDUSTRIAL_PROXIMITY: float = 0.20
    RISK_WEIGHT_CONFIDENCE: float = 0.15

    # Data paths
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    SAMPLE_DATA_DIR: Path = DATA_DIR / "sample"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

settings = Settings()

# Ensure directories exist
settings.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
