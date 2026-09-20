from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.models.osm_context import EnrichedThermalAnomaly
from backend.app.models.thermal_classification import SeverityLevel

class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class RiskAssessment(BaseModel):
    """Explainable Risk Engine assessment payload for a thermal anomaly observation."""
    composite_risk_score: float = Field(..., ge=0.0, le=100.0, description="Normalized multi-factor risk score (0.0 - 100.0)")
    risk_level: RiskLevel = Field(..., description="Overall risk rating (CRITICAL, HIGH, MEDIUM, LOW)")
    action_recommendation: str = Field(..., description="Actionable operational emergency recommendation")
    risk_factors: Dict[str, Any] = Field(..., description="Risk factor values, availability, and contributions")
    explanation: str = Field(..., description="Transparent explanation detailing why the anomaly is considered risky")
    factors: Dict[str, Any] = Field(default_factory=dict, description="Explainable factor values and availability")
    source: str = Field(default="THERMOSENTRY Risk Engine", description="Risk assessment provenance")

class DecisionIntelligenceAnomaly(EnrichedThermalAnomaly):
    """Full decision intelligence model synthesizing satellite detection, AI classification, persistence, OSM context, and risk assessment."""
    risk_assessment: RiskAssessment = Field(..., description="Multi-factor risk assessment and operational recommendations")

class DecisionIntelligenceSummary(BaseModel):
    """Aggregated global metrics and threat summary across thermal anomaly detections."""
    total_anomalies: int = Field(..., description="Total thermal anomaly observations evaluated")
    critical_alerts_count: int = Field(..., description="Count of CRITICAL risk anomalies requiring immediate action")
    high_risk_count: int = Field(..., description="Count of HIGH risk anomalies requiring priority monitoring")
    persistent_sources_count: int = Field(..., description="Count of persistent thermal sources identified")
    industrial_proximity_count: int = Field(..., description="Count of anomalies near critical industrial infrastructure")
    category_breakdown: Dict[str, int] = Field(..., description="Distribution count by AI event category")

class DecisionIntelligenceResponse(BaseModel):
    """Primary unified REST API payload for THERMOSENTRY AI Decision Intelligence."""
    status: str = Field("success", description="Response status")
    source: str = Field(..., description="Data provenance description")
    timestamp: str = Field(..., description="Response generation timestamp")
    summary: DecisionIntelligenceSummary = Field(..., description="Global threat summary metrics")
    data: List[DecisionIntelligenceAnomaly] = Field(..., description="List of decision intelligence anomaly records")
