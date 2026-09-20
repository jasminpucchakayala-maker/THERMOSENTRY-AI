from fastapi import APIRouter, Query, Body
from typing import List, Optional
from backend.app.models.thermal_classification import ClassifiedThermalAnomaly
from backend.app.models.persistence import (
    PersistentThermalAnomaly,
    PersistentAnomalyResponse,
    PersistentClusterResponse
)
from backend.app.services.persistence_service import persistence_service
from backend.app.ml.persistence_engine import persistence_engine

router = APIRouter(prefix="/api", tags=["Persistent Thermal Source Detection"])

@router.get("/persistent-anomalies", response_model=PersistentAnomalyResponse, summary="Get Persistent Thermal Anomalies")
async def get_persistent_anomalies_endpoint(
    days: int = Query(default=1, ge=1, le=10, description="Number of past days to query"),
    source: str = Query(default="VIIRS_SNPP_NRT", description="FIRMS Satellite source"),
    country: str = Query(default="IND", description="ISO3 Country Code"),
    use_cache: bool = Query(default=True, description="Allow falling back to cached/sample data if offline"),
    only_persistent: bool = Query(default=False, description="Filter to return only persistent thermal sources")
):
    """
    Analyzes satellite thermal anomalies for spatial-temporal recurrence.
    Returns classified anomaly data enriched with persistence scores, cluster IDs, and persistence types.
    """
    return await persistence_service.get_persistent_thermal_anomalies(
        days=days,
        source=source,
        country=country,
        use_cache=use_cache,
        only_persistent=only_persistent
    )

@router.get("/persistent-clusters", response_model=PersistentClusterResponse, summary="Get Persistent Hotspot Clusters")
async def get_persistent_clusters_endpoint(
    days: int = Query(default=1, ge=1, le=10, description="Number of past days to query"),
    source: str = Query(default="VIIRS_SNPP_NRT", description="FIRMS Satellite source"),
    country: str = Query(default="IND", description="ISO3 Country Code"),
    use_cache: bool = Query(default=True, description="Allow falling back to cached/sample data if offline")
):
    """
    Returns aggregated spatial cluster centroids and persistence indicators across thermal detections.
    """
    return await persistence_service.get_persistent_clusters(
        days=days,
        source=source,
        country=country,
        use_cache=use_cache
    )

@router.post("/analyze-persistence", response_model=List[PersistentThermalAnomaly], summary="Analyze Persistence on Demand")
async def analyze_persistence_endpoint(
    anomalies: List[ClassifiedThermalAnomaly] = Body(..., description="List of classified thermal anomalies to cluster")
):
    """
    Runs spatial clustering and persistence analysis over an arbitrary list of classified thermal anomaly payloads.
    """
    persistent_anomalies, _ = persistence_engine.analyze_clusters(anomalies)
    return persistent_anomalies
