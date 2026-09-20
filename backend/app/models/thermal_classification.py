from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from backend.app.models.thermal_anomaly import ThermalAnomaly

class EventCategory(str, Enum):
    WILDFIRE = "Wildfire"
    INDUSTRIAL_FLARE = "Industrial Flare / Processing"
    AGRICULTURAL_BURNING = "Agricultural Burning"
    URBAN_LANDFILL = "Urban / Landfill Fire"
    VOLCANIC_ACTIVITY = "Volcanic Activity"
    SOLAR_GLINT_NOISE = "Solar Glint / False Positive"

class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ThermalClassification(BaseModel):
    """AI Classification metadata for a thermal anomaly observation."""
    category: EventCategory = Field(..., description="Predicted thermal event category")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI classification probability score (0.0 - 1.0)")
    severity_level: SeverityLevel = Field(..., description="Assessed thermal risk severity level")
    features: Dict[str, float] = Field(..., description="Extracted numerical features used for classification decision")
    explanation: str = Field(..., description="Human-readable decision rationale explaining the classification")
    method: str = Field(default="baseline", description="Classification method; baseline means transparent rule-based logic")
    evidence: List[str] = Field(default_factory=list, description="Observed evidence used by the classifier")
    reasoning: str = Field(default="", description="Transparent classification reasoning")
    class_name: str = Field(default="Uncertain Anomaly", alias="class", description="Canonical frontend classification label")

    model_config = {"populate_by_name": True}

class ClassifiedThermalAnomaly(ThermalAnomaly):
    """Thermal anomaly combined with AI classification results."""
    classification: ThermalClassification = Field(..., description="AI event classification & risk metadata")

class ClassifiedAnomalyResponse(BaseModel):
    """API response model for classified thermal anomaly queries."""
    status: str = Field("success", description="Response status")
    count: int = Field(..., description="Total count of classified thermal anomalies")
    source: str = Field(..., description="Data source provenance")
    timestamp: str = Field(..., description="Response generation timestamp")
    data: List[ClassifiedThermalAnomaly] = Field(..., description="List of classified thermal anomalies")
