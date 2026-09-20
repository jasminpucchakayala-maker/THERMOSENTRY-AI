import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BACKEND_DIR / "data"


def _env_value(name: str, default: str):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _env_int(name: str, default: int) -> int:
    value = _env_value(name, str(default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    value = _env_value(name, str(default))
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class Settings(BaseSettings):
    APP_NAME: str = "THERMOSENTRY AI"
    APP_ENV: str = _env_value("APP_ENV", "development")
    LOG_LEVEL: str = _env_value("LOG_LEVEL", "INFO")

    # NASA FIRMS API settings
    FIRMS_API_KEY: str = _env_value("FIRMS_API_KEY", "")
    FIRMS_BASE_URL: str = _env_value("FIRMS_BASE_URL", "https://firms.modaps.eosdis.nasa.gov/api/")
    FIRMS_DEFAULT_SOURCE: str = _env_value("FIRMS_DEFAULT_SOURCE", "VIIRS_SNPP_NRT")
    FIRMS_DEFAULT_DAYS: int = _env_int("FIRMS_DEFAULT_DAYS", 1)
    FIRMS_DEFAULT_COUNTRY: str = _env_value("FIRMS_DEFAULT_COUNTRY", "IND")
    FIRMS_TIMEOUT_SECONDS: float = _env_float("FIRMS_TIMEOUT_SECONDS", 15.0)

    # Persistence analysis settings
    PERSISTENCE_DISTANCE_THRESHOLD_KM: float = _env_float("PERSISTENCE_DISTANCE_THRESHOLD_KM", 1.0)
    PERSISTENCE_TIME_WINDOW_DAYS: int = _env_int("PERSISTENCE_TIME_WINDOW_DAYS", 10)

    # OpenStreetMap Overpass settings
    OVERPASS_URL: str = _env_value("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
    OSM_SEARCH_RADIUS_KM: float = _env_float("OSM_SEARCH_RADIUS_KM", 5.0)
    OSM_TIMEOUT_SECONDS: float = _env_float("OSM_TIMEOUT_SECONDS", 6.0)

    # Risk weights are configurable, but unavailable factors are never scored.
    RISK_WEIGHT_THERMAL_INTENSITY: float = _env_float("RISK_WEIGHT_THERMAL_INTENSITY", 0.45)
    RISK_WEIGHT_PERSISTENCE: float = _env_float("RISK_WEIGHT_PERSISTENCE", 0.20)
    RISK_WEIGHT_INDUSTRIAL_PROXIMITY: float = _env_float("RISK_WEIGHT_INDUSTRIAL_PROXIMITY", 0.20)
    RISK_WEIGHT_CONFIDENCE: float = _env_float("RISK_WEIGHT_CONFIDENCE", 0.15)

    # Data paths
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    SAMPLE_DATA_DIR: Path = DATA_DIR / "sample"

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()

# Ensure directories exist
settings.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
