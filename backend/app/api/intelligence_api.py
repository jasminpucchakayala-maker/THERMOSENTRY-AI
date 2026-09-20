from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.app.services.risk_service import risk_service
from backend.app.services.classification_service import classification_service
from backend.app.services.persistence_service import persistence_service
from backend.app.services.osm_service import osm_service
from backend.app.ml.risk_engine import risk_engine

router = APIRouter(prefix="/api", tags=["Event Intelligence"])


async def _event(event_id: str, days: int = 1, source: str = "VIIRS_SNPP_NRT", country: str = "IND", use_cache: bool = True, use_live_osm: bool = False):
    try:
        return await risk_service.get_decision_event(event_id, days=days, source=source, country=country, use_cache=use_cache, use_live_osm=use_live_osm)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/classification/{event_id}")
async def get_classification(event_id: str, days: int = Query(1, ge=1, le=10), source: str = "VIIRS_SNPP_NRT", country: str = "IND", use_cache: bool = True):
    item = await _event(event_id, days, source, country, use_cache)
    return item.classification


@router.get("/persistence/{event_id}")
async def get_persistence(event_id: str, days: int = Query(1, ge=1, le=10), source: str = "VIIRS_SNPP_NRT", country: str = "IND", use_cache: bool = True):
    item = await _event(event_id, days, source, country, use_cache)
    return item.persistence


@router.get("/industrial-context/{event_id}")
async def get_industrial_context(event_id: str, days: int = Query(1, ge=1, le=10), source: str = "VIIRS_SNPP_NRT", country: str = "IND", use_cache: bool = True, use_live_osm: bool = Query(default=False)):
    item = await _event(event_id, days, source, country, use_cache, use_live_osm)
    return item.industrial_context


@router.get("/risk/{event_id}")
async def get_risk(event_id: str, days: int = Query(1, ge=1, le=10), source: str = "VIIRS_SNPP_NRT", country: str = "IND", use_cache: bool = True):
    item = await _event(event_id, days, source, country, use_cache)
    return item.risk_assessment


@router.get("/decision/{event_id}")
async def get_decision(event_id: str, days: int = Query(1, ge=1, le=10), source: str = "VIIRS_SNPP_NRT", country: str = "IND", use_cache: bool = True, use_live_osm: bool = Query(default=False)):
    return await _event(event_id, days, source, country, use_cache, use_live_osm)