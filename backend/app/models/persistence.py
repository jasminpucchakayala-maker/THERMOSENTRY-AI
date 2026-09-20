from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.models.thermal_classification import ClassifiedThermalAnomaly

class PersistenceType(str, Enum):
    HIGHLY_PERSISTENT_INDUSTRIAL = "Highly Persistent Industrial Source"
    RECURRING_SEASONAL = "Recurring / Seasonal Burning"
    TRANSIENT_EVENT = "Transient Fire Event"

class PersistenceInfo(BaseModel):
    """Persistence analysis metadata for a thermal anomaly observation."""
    cluster_id: str = Field(..., description="Unique spatial cluster hash ID")
    is_persistent: bool = Field(..., description="True if anomaly belongs to a recurring/persistent thermal source")
    persistence_score: float = Field(..., ge=0.0, le=1.0, description="Persistence index score (0.0 - 1.0)")
    persistence_type: PersistenceType = Field(..., description="Categorized persistence classification")
    observation_count: int = Field(..., ge=1, description="Total historical detections recorded within cluster radius")
    first_seen: str = Field(..., description="Earliest detection date (YYYY-MM-DD)")
    last_seen: str = Field(..., description="Most recent detection date (YYYY-MM-DD)")
    duration_days: int = Field(..., ge=0, description="Active temporal span in days between first and last detection")
    radius_km: float = Field(default=1.0, description="Cluster spatial proximity radius in kilometers")
    description: str = Field(..., description="Human-readable explanation of persistence finding")

class PersistentThermalAnomaly(ClassifiedThermalAnomaly):
    """Classified thermal anomaly combined with persistence analysis metadata."""
    persistence: PersistenceInfo = Field(..., description="Spatial-temporal persistence analysis")

class PersistentCluster(BaseModel):
    """Aggregated spatial cluster summary for persistent hotspot sources."""
    cluster_id: str = Field(..., description="Cluster identifier")
    centroid_latitude: float = Field(..., ge=-90.0, le=90.0, description="Cluster centroid latitude")
    centroid_longitude: float = Field(..., ge=-180.0, le=180.0, description="Cluster centroid longitude")
    observation_count: int = Field(..., ge=1, description="Total detections in cluster")
    is_persistent: bool = Field(..., description="Persistence flag")
    persistence_score: float = Field(..., ge=0.0, le=1.0, description="Persistence score (0.0 - 1.0)")
    persistence_type: PersistenceType = Field(..., description="Persistence classification")
    first_seen: str = Field(..., description="First observation date")
    last_seen: str = Field(..., description="Last observation date")
    avg_frp: float = Field(..., description="Average Fire Radiative Power (MW)")
    max_brightness: float = Field(..., description="Maximum brightness temperature (K)")

class PersistentAnomalyResponse(BaseModel):
    """API response model for persistent thermal anomaly queries."""
    status: str = Field("success", description="Response status")
    count: int = Field(..., description="Total count of anomalies")
    persistent_count: int = Field(..., description="Count of persistent thermal anomalies identified")
    source: str = Field(..., description="Data provenance description")
    timestamp: str = Field(..., description="Response generation timestamp")
    data: List[PersistentThermalAnomaly] = Field(..., description="List of persistent thermal anomalies")

class PersistentClusterResponse(BaseModel):
    """API response model for persistent hotspot clusters."""
    status: str = Field("success", description="Response status")
    count: int = Field(..., description="Total number of hotspot clusters")
    persistent_clusters_count: int = Field(..., description="Number of persistent industrial clusters")
    timestamp: str = Field(..., description="Response timestamp")
    clusters: List[PersistentCluster] = Field(..., description="List of persistent clusters")
