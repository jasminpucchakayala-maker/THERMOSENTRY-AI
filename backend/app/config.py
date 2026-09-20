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
