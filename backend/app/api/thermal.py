from fastapi import APIRouter, Query
from typing import Optional
from backend.app.config import settings
from backend.app.models.thermal_anomaly import ThermalAnomalyResponse
from backend.app.services.firms_service import firms_service

router = APIRouter(prefix="/api", tags=["Thermal Anomalies"])

@router.get("/health", summary="System Health Check")
async def health_check():
    """Returns the operational status of the THERMOSENTRY AI backend."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "firms_configured": bool(settings.FIRMS_API_KEY.strip())
    }

@router.get("/thermal-anomalies", response_model=ThermalAnomalyResponse, summary="Get Normalized Thermal Anomalies")
async def get_thermal_anomalies_endpoint(
    days: int = Query(default=1, ge=1, le=10, description="Number of past days to query (1-10)"),
    source: str = Query(default="VIIRS_SNPP_NRT", description="FIRMS Satellite source (e.g. VIIRS_SNPP_NRT, MODIS_NRT)"),
    country: str = Query(default="IND", description="ISO3 Country Code (e.g. IND, USA)"),
    use_cache: bool = Query(default=True, description="Allow falling back to cached/sample data if API is unavailable")
):
    """
    Fetches, cleans, normalizes, and returns satellite thermal anomaly observations.
    Supported NASA FIRMS sources include: VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT, VIIRS_NOAA21_NRT, MODIS_NRT.
    """
    return await firms_service.get_thermal_anomalies(
        days=days,
        source=source,
        country=country,
        use_cache=use_cache
    )
