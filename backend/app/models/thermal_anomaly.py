import hashlib
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator

class ThermalAnomaly(BaseModel):
    """Normalized thermal anomaly data model representing a satellite detection event."""
    id: str = Field(..., description="Unique hash ID derived from anomaly spatial-temporal attributes")
    firms_id: Optional[str] = Field(default=None, description="Original NASA FIRMS record identifier when provided")
    event_id: Optional[str] = Field(default=None, description="Deterministic THERMOSENTRY internal event identifier")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate in WGS84")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate in WGS84")
    acquisition_date: str = Field(..., description="Acquisition date (YYYY-MM-DD)")
    acquisition_time: str = Field(..., description="Acquisition time (HHMM format)")
    satellite: str = Field(..., description="Satellite platform name (e.g., VIIRS, MODIS, N20, N21)")
    instrument: str = Field(..., description="Instrument sensor name (e.g., VIIRS, MODIS)")
    confidence: Optional[float] = Field(default=None, description="Detection confidence percentage (0-100) or scaled score")
    brightness_temperature: Optional[float] = Field(default=None, description="Brightness temperature in Kelvin")
    frp: Optional[float] = Field(default=None, description="Fire Radiative Power in Megawatts (MW)")
    day_night: Optional[str] = Field(default=None, description="Day ('D') or Night ('N') indicator")
    source: str = Field(..., description="NASA FIRMS product source identifier")

    @classmethod
    def generate_id(cls, lat: float, lon: float, date: str, time: str, satellite: str) -> str:
        """Generates a consistent unique ID hash for spatial-temporal deduplication."""
        raw_str = f"{lat:.4f}_{lon:.4f}_{date}_{time}_{satellite.upper()}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]

class ThermalAnomalyResponse(BaseModel):
    """API Response payload wrapper for thermal anomaly datasets."""
    status: str = Field("success", description="Status of the request")
    count: int = Field(..., description="Total count of validated records")
    source: str = Field(..., description="Data provenance description (Live API, Local Cache, or Sample Data)")
    timestamp: str = Field(..., description="Response generation timestamp")
    data: List[ThermalAnomaly] = Field(..., description="List of normalized thermal anomaly objects")
