import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BACKEND_DIR / "data"

class Settings(BaseSettings):
    APP_NAME: str = "THERMOSENTRY AI"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # NASA FIRMS API settings
    FIRMS_API_KEY: str = os.getenv("FIRMS_API_KEY", "")
    FIRMS_BASE_URL: str = os.getenv("FIRMS_BASE_URL", "https://firms.modaps.eosdis.nasa.gov/api/")
    FIRMS_DEFAULT_SOURCE: str = os.getenv("FIRMS_DEFAULT_SOURCE", "VIIRS_SNPP_NRT")
    FIRMS_DEFAULT_DAYS: int = int(os.getenv("FIRMS_DEFAULT_DAYS", "1"))
    FIRMS_DEFAULT_COUNTRY: str = os.getenv("FIRMS_DEFAULT_COUNTRY", "IND")
    FIRMS_TIMEOUT_SECONDS: float = float(os.getenv("FIRMS_TIMEOUT_SECONDS", "15"))

    # Persistence analysis settings
    PERSISTENCE_DISTANCE_THRESHOLD_KM: float = float(os.getenv("PERSISTENCE_DISTANCE_THRESHOLD_KM", "1.0"))
    PERSISTENCE_TIME_WINDOW_DAYS: int = int(os.getenv("PERSISTENCE_TIME_WINDOW_DAYS", "10"))

    # OpenStreetMap Overpass settings
    OVERPASS_URL: str = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
    OSM_SEARCH_RADIUS_KM: float = float(os.getenv("OSM_SEARCH_RADIUS_KM", "5.0"))
    OSM_TIMEOUT_SECONDS: float = float(os.getenv("OSM_TIMEOUT_SECONDS", "6"))

    # Risk weights are configurable, but unavailable factors are never scored.
    RISK_WEIGHT_THERMAL_INTENSITY: float = float(os.getenv("RISK_WEIGHT_THERMAL_INTENSITY", "0.45"))
    RISK_WEIGHT_PERSISTENCE: float = float(os.getenv("RISK_WEIGHT_PERSISTENCE", "0.20"))
    RISK_WEIGHT_INDUSTRIAL_PROXIMITY: float = float(os.getenv("RISK_WEIGHT_INDUSTRIAL_PROXIMITY", "0.20"))
    RISK_WEIGHT_CONFIDENCE: float = float(os.getenv("RISK_WEIGHT_CONFIDENCE", "0.15"))

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
