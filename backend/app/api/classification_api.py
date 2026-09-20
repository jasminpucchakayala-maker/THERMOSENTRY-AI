from fastapi import APIRouter, Query, Body
from typing import Optional
from backend.app.models.thermal_anomaly import ThermalAnomaly
from backend.app.models.thermal_classification import ClassifiedThermalAnomaly, ClassifiedAnomalyResponse
from backend.app.services.classification_service import classification_service
from backend.app.ml.classifier import classifier

router = APIRouter(prefix="/api", tags=["AI Thermal Classification"])

@router.get("/classified-anomalies", response_model=ClassifiedAnomalyResponse, summary="Get AI Classified Thermal Anomalies")
async def get_classified_anomalies_endpoint(
    days: int = Query(default=1, ge=1, le=10, description="Number of past days to query"),
    source: str = Query(default="VIIRS_SNPP_NRT", description="FIRMS Satellite source"),
    country: str = Query(default="IND", description="ISO3 Country Code"),
    use_cache: bool = Query(default=True, description="Allow falling back to cached/sample data if offline"),
    min_severity: Optional[str] = Query(default=None, description="Filter by minimum severity level (CRITICAL, HIGH, MEDIUM, LOW)")
):
    """
    Retrieves satellite thermal anomalies and applies the AI Thermal Classifier engine.
    Returns classified thermal event categories, confidence probability, severity rating, and explainable breakdown.
    """
    return await classification_service.get_classified_thermal_anomalies(
        days=days,
        source=source,
        country=country,
        use_cache=use_cache,
        min_severity=min_severity
    )

@router.post("/classify-single", response_model=ClassifiedThermalAnomaly, summary="Classify Single Thermal Anomaly Payload")
async def classify_single_anomaly_endpoint(
    anomaly: ThermalAnomaly = Body(..., description="Thermal anomaly object payload to classify")
):
    """
    Evaluates and classifies a single raw or custom thermal anomaly payload on demand.
    """
    return classifier.classify_classified_anomaly(anomaly)
