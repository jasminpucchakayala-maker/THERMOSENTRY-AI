from datetime import datetime
from typing import List, Optional, Tuple
from backend.app.config import settings
from backend.app.models.persistence import (
    PersistentThermalAnomaly,
    PersistentCluster,
    PersistentAnomalyResponse,
    PersistentClusterResponse
)
from backend.app.services.classification_service import classification_service
from backend.app.ml.persistence_engine import persistence_engine
from backend.app.utils.logging_config import logger

class PersistenceService:
    """Service handling persistent thermal source detection and spatial cluster aggregation."""

    def __init__(self):
        self.classification_service = classification_service
        self.persistence_engine = persistence_engine

    async def get_persistent_thermal_anomalies(
        self,
        days: int = settings.FIRMS_DEFAULT_DAYS,
        source: str = settings.FIRMS_DEFAULT_SOURCE,
        country: str = settings.FIRMS_DEFAULT_COUNTRY,
        use_cache: bool = True,
        only_persistent: bool = False
    ) -> PersistentAnomalyResponse:
        """
        Fetches classified thermal anomalies and executes spatial-temporal persistence clustering.
        """
        classified_res = await self.classification_service.get_classified_thermal_anomalies(
            days=days,
            source=source,
            country=country,
            use_cache=use_cache
        )

        persistent_anomalies, _ = self.persistence_engine.analyze_clusters(classified_res.data)

        if only_persistent:
            persistent_anomalies = [item for item in persistent_anomalies if item.persistence.is_persistent]

        persistent_count = sum(1 for item in persistent_anomalies if item.persistence.is_persistent)

        logger.info(f"Persistence analysis complete: {len(persistent_anomalies)} records analyzed, {persistent_count} persistent sources identified.")

        return PersistentAnomalyResponse(
            status="success",
            count=len(persistent_anomalies),
            persistent_count=persistent_count,
            source=classified_res.source,
            timestamp=datetime.now().isoformat(),
            data=persistent_anomalies
        )

    async def get_persistent_clusters(
        self,
        days: int = settings.FIRMS_DEFAULT_DAYS,
        source: str = settings.FIRMS_DEFAULT_SOURCE,
        country: str = settings.FIRMS_DEFAULT_COUNTRY,
        use_cache: bool = True
    ) -> PersistentClusterResponse:
        """
        Returns aggregated persistent hotspot clusters and spatial centroids.
        """
        classified_res = await self.classification_service.get_classified_thermal_anomalies(
            days=days,
            source=source,
            country=country,
            use_cache=use_cache
        )

        _, clusters = self.persistence_engine.analyze_clusters(classified_res.data)
        persistent_clusters_count = sum(1 for c in clusters if c.is_persistent)

        return PersistentClusterResponse(
            status="success",
            count=len(clusters),
            persistent_clusters_count=persistent_clusters_count,
            timestamp=datetime.now().isoformat(),
            clusters=clusters
        )

persistence_service = PersistenceService()
