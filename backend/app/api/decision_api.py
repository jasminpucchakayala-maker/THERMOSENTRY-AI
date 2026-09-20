from fastapi import APIRouter, Query, Body
from typing import Optional
from backend.app.models.osm_context import EnrichedThermalAnomaly
from backend.app.models.decision_intelligence import (
    DecisionIntelligenceAnomaly,
    DecisionIntelligenceResponse,
    RiskAssessment
)
from backend.app.services.risk_service import risk_service
from backend.app.ml.risk_engine import risk_engine

router = APIRouter(prefix="/api", tags=["Decision Intelligence Pipeline"])

@router.get("/decision-intelligence", response_model=DecisionIntelligenceResponse, summary="Get Full Decision Intelligence Pipeline Payload")
async def get_decision_intelligence_endpoint(
    days: int = Query(default=1, ge=1, le=10, description="Number of past days to query"),
    source: str = Query(default="VIIRS_SNPP_NRT", description="FIRMS Satellite source"),
    country: str = Query(default="IND", description="ISO3 Country Code"),
    use_cache: bool = Query(default=True, description="Allow falling back to cached/sample data if offline"),
    use_live_osm: bool = Query(default=True, description="Use live OpenStreetMap Overpass API"),
    min_risk_level: Optional[str] = Query(default=None, description="Filter by minimum risk level (CRITICAL, HIGH, MEDIUM, LOW)")
):
    """
    Primary Unified Endpoint for THERMOSENTRY AI.
    Executes the full satellite-to-decision intelligence pipeline:
    NASA FIRMS Ingestion → AI Thermal Classification → Persistent Hotspot Detection → OpenStreetMap Industrial Context → Explainable Risk Engine.
    """
    return await risk_service.get_decision_intelligence(
        days=days,
        source=source,
        country=country,
        use_cache=use_cache,
        use_live_osm=use_live_osm,
        min_risk_level=min_risk_level
    )

@router.get("/alerts", response_model=DecisionIntelligenceResponse, summary="Get Active Critical & High Risk Alerts")
async def get_active_alerts_endpoint(
    days: int = Query(default=1, ge=1, le=10, description="Number of past days to query"),
    source: str = Query(default="VIIRS_SNPP_NRT", description="FIRMS Satellite source"),
    country: str = Query(default="IND", description="ISO3 Country Code"),
    use_cache: bool = Query(default=True, description="Allow falling back to cached/sample data if offline"),
    use_live_osm: bool = Query(default=True, description="Use live OpenStreetMap Overpass API")
):
    """
    Returns high-priority monitoring alerts filtered to CRITICAL and HIGH risk events requiring operational response.
    """
    return await risk_service.get_active_alerts(
        days=days,
        source=source,
        country=country,
        use_cache=use_cache,
        use_live_osm=use_live_osm
    )

@router.post("/analyze-event", response_model=DecisionIntelligenceAnomaly, summary="Analyze Custom Anomaly Event")
async def analyze_custom_event_endpoint(
    anomaly: EnrichedThermalAnomaly = Body(..., description="Enriched thermal anomaly payload to evaluate")
):
    """
    Evaluates a single thermal anomaly event payload on demand, calculating composite risk score and operational recommendations.
    """
    return risk_engine.evaluate_decision_anomaly(anomaly)
