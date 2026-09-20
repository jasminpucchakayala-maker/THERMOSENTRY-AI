import asyncio
from datetime import datetime
from typing import List, Optional
from backend.app.config import settings
from backend.app.models.osm_context import EnrichedThermalAnomaly, EnrichedAnomalyResponse, OSMIndustrialContext
from backend.app.services.persistence_service import persistence_service
from backend.app.ml.osm_engine import osm_engine
from backend.app.utils.logging_config import logger

class OSMService:
    """Service enriching thermal anomalies with OpenStreetMap industrial context."""

    def __init__(self):
        self.persistence_service = persistence_service
        self.osm_engine = osm_engine

    async def enrich_anomalies_with_industrial_context(
        self,
        days: int = settings.FIRMS_DEFAULT_DAYS,
        source: str = settings.FIRMS_DEFAULT_SOURCE,
        country: str = settings.FIRMS_DEFAULT_COUNTRY,
        use_cache: bool = True,
        use_live_osm: bool = True
    ) -> EnrichedAnomalyResponse:
        """
        Retrieves persistent thermal anomalies and enriches each observation with nearby industrial context.
        """
        persistent_res = await self.persistence_service.get_persistent_thermal_anomalies(
            days=days,
            source=source,
            country=country,
            use_cache=use_cache
        )

        anomalies = persistent_res.data
        enriched_list: List[EnrichedThermalAnomaly] = []

        # Run asynchronous OSM context queries concurrently
        tasks = [
            self.osm_engine.get_industrial_context(a.latitude, a.longitude, use_live=use_live_osm)
            for a in anomalies
        ]
        contexts: List[OSMIndustrialContext] = await asyncio.gather(*tasks, return_exceptions=True)

        safe_contexts: List[OSMIndustrialContext] = []
        for ctx in contexts:
            if isinstance(ctx, OSMIndustrialContext):
                safe_contexts.append(ctx)
            else:
                logger.warning(f"OSM context lookup failed for one anomaly: {ctx}")
                safe_contexts.append(await self.osm_engine.get_industrial_context(0.0, 0.0, use_live=False))

        for anomaly, ctx in zip(anomalies, safe_contexts):
            enriched = EnrichedThermalAnomaly(
                **anomaly.model_dump(),
                industrial_context=ctx
            )
            enriched_list.append(enriched)

        ind_count = sum(1 for item in enriched_list if item.industrial_context.has_nearby_industrial)

        logger.info(f"OSM Enrichment complete: {len(enriched_list)} records processed, {ind_count} with nearby industrial infrastructure.")

        return EnrichedAnomalyResponse(
            status="success",
            count=len(enriched_list),
            industrial_proximity_count=ind_count,
            source=persistent_res.source,
            timestamp=datetime.now().isoformat(),
            data=enriched_list
        )

osm_service = OSMService()
