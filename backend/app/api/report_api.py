from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from backend.app.services.risk_service import risk_service
from backend.app.services.report_service import report_service

router = APIRouter(prefix="/api", tags=["Reports"])


@router.get("/reports/{event_id}", summary="Generate HTML Intelligence Report")
async def generate_report(event_id: str, days: int = Query(1, ge=1, le=10), source: str = "VIIRS_SNPP_NRT", country: str = "IND", use_cache: bool = True, use_live_osm: bool = Query(default=False)):
    try:
        item = await risk_service.get_decision_event(event_id, days=days, source=source, country=country, use_cache=use_cache, use_live_osm=use_live_osm)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    filename = f"thermosentry-{item.event_id or item.id}.html"
    return Response(
        content=report_service.render_html(item),
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )