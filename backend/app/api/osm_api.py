from fastapi import APIRouter, Query
from typing import Optional
from backend.app.models.osm_context import OSMIndustrialContext, EnrichedAnomalyResponse
from backend.app.services.osm_service import osm_service
from backend.app.ml.osm_engine import osm_engine

router = APIRouter(prefix="/api", tags=["OpenStreetMap Industrial Context"])

@router.get("/enriched-anomalies", response_model=EnrichedAnomalyResponse, summary="Get Full Enriched Thermal Anomalies")
async def get_enriched_anomalies_endpoint(
    days: int = Query(default=1, ge=1, le=10, description="Number of past days to query"),
    source: str = Query(default="VIIRS_SNPP_NRT", description="FIRMS Satellite source"),
    country: str = Query(default="IND", description="ISO3 Country Code"),
    use_cache: bool = Query(default=True, description="Allow falling back to cached/sample FIRMS data if offline"),
    use_live_osm: bool = Query(default=True, description="Query live OpenStreetMap Overpass API (falls back to local cache if offline)")
):
    """
    Primary pipeline endpoint: Ingests satellite thermal observations, executes AI Classification, 
    evaluates Persistent Hotspot Clusters, and enriches each detection with OpenStreetMap Industrial Infrastructure Context.
    """
    return await osm_service.enrich_anomalies_with_industrial_context(
        days=days,
        source=source,
        country=country,
        use_cache=use_cache,
        use_live_osm=use_live_osm
    )

@router.get("/nearby-industrial", response_model=OSMIndustrialContext, summary="Get Nearby Industrial Facilities")
async def get_nearby_industrial_endpoint(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate"),
    use_live: bool = Query(default=True, description="Use live OpenStreetMap Overpass API")
):
    """
    Queries nearby oil refineries, chemical plants, power stations, gas terminals, and industrial zones around specified coordinates.
    """
    return await osm_engine.get_industrial_context(lat=lat, lon=lon, use_live=use_live)
