from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.models.persistence import PersistentThermalAnomaly

class IndustrialFacility(BaseModel):
    """Industrial infrastructure facility model from OpenStreetMap."""
    name: str = Field(..., description="Name of the facility or industrial site")
    type: str = Field(..., description="Category (e.g., Oil Refinery, Power Plant, Chemical Complex, Industrial Zone)")
    distance_km: float = Field(..., ge=0.0, description="Spatial distance from thermal anomaly in kilometers")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Facility latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Facility longitude coordinate")
    osm_id: Optional[str] = Field(default=None, description="OpenStreetMap Element ID if available")
    tags: Dict[str, str] = Field(default_factory=dict, description="Raw OSM Key-Value tags")

class OSMIndustrialContext(BaseModel):
    """Industrial context metadata associated with a thermal anomaly observation."""
    has_nearby_industrial: bool = Field(..., description="True if industrial infrastructure exists within 5.0 km radius")
    nearest_facility_name: Optional[str] = Field(default=None, description="Name of the closest industrial facility")
    nearest_facility_type: Optional[str] = Field(default=None, description="Type of the closest industrial facility")
    distance_to_nearest_km: Optional[float] = Field(default=None, description="Distance to closest facility in kilometers")
    facilities_within_3km: int = Field(default=0, description="Count of industrial facilities within 3.0 km")
    facilities_within_5km: int = Field(default=0, description="Count of industrial facilities within 5.0 km")
    nearby_facilities: List[IndustrialFacility] = Field(default_factory=list, description="List of nearby facilities sorted by distance")
    risk_modifier: float = Field(default=1.0, ge=0.5, le=3.0, description="Risk multiplier contribution for downstream Risk Engine")
    source: str = Field(..., description="Data provenance (e.g. OpenStreetMap Overpass API or Local Infrastructure Cache)")

class EnrichedThermalAnomaly(PersistentThermalAnomaly):
    """Thermal anomaly enriched with AI classification, persistence, and OpenStreetMap industrial context."""
    industrial_context: OSMIndustrialContext = Field(..., description="Nearby OpenStreetMap industrial infrastructure context")

class EnrichedAnomalyResponse(BaseModel):
    """API response model for fully enriched thermal anomaly queries."""
    status: str = Field("success", description="Response status")
    count: int = Field(..., description="Total count of anomalies")
    industrial_proximity_count: int = Field(..., description="Count of anomalies with nearby industrial facilities")
    source: str = Field(..., description="Data provenance description")
    timestamp: str = Field(..., description="Response generation timestamp")
    data: List[EnrichedThermalAnomaly] = Field(..., description="List of enriched thermal anomalies")
