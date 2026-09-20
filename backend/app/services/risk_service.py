from datetime import datetime
from typing import List, Optional, Dict
from backend.app.config import settings
from backend.app.models.decision_intelligence import (
    RiskLevel,
    DecisionIntelligenceAnomaly,
    DecisionIntelligenceSummary,
    DecisionIntelligenceResponse
)
from backend.app.services.osm_service import osm_service
from backend.app.ml.risk_engine import risk_engine
from backend.app.utils.logging_config import logger

class RiskService:
    """Service coordinating end-to-end decision intelligence generation and risk assessment."""

    def __init__(self):
        self.osm_service = osm_service
        self.risk_engine = risk_engine

    async def get_decision_intelligence(
        self,
        days: int = settings.FIRMS_DEFAULT_DAYS,
        source: str = settings.FIRMS_DEFAULT_SOURCE,
        country: str = settings.FIRMS_DEFAULT_COUNTRY,
        use_cache: bool = True,
        use_live_osm: bool = True,
        min_risk_level: Optional[str] = None
    ) -> DecisionIntelligenceResponse:
        """
        Executes the complete THERMOSENTRY AI Decision Intelligence Pipeline:
        NASA FIRMS Ingestion → AI Thermal Classification → Persistence Detection → OSM Industrial Context → Explainable Risk Assessment.
        """
        enriched_res = await self.osm_service.enrich_anomalies_with_industrial_context(
            days=days,
            source=source,
            country=country,
            use_cache=use_cache,
            use_live_osm=use_live_osm
        )

        anomalies = enriched_res.data
        decision_anomalies: List[DecisionIntelligenceAnomaly] = []

        for a in anomalies:
            decision_item = self.risk_engine.evaluate_decision_anomaly(a)
            decision_anomalies.append(decision_item)

        # Calculate Global Threat Summary Metrics
        critical_count = sum(1 for item in decision_anomalies if item.risk_assessment.risk_level == RiskLevel.CRITICAL)
        high_count = sum(1 for item in decision_anomalies if item.risk_assessment.risk_level == RiskLevel.HIGH)
        persistent_count = sum(1 for item in decision_anomalies if item.persistence.is_persistent)
        industrial_count = sum(1 for item in decision_anomalies if item.industrial_context.has_nearby_industrial)

        cat_breakdown: Dict[str, int] = {}
        for item in decision_anomalies:
            cat_name = item.classification.category.value
            cat_breakdown[cat_name] = cat_breakdown.get(cat_name, 0) + 1

        summary = DecisionIntelligenceSummary(
            total_anomalies=len(decision_anomalies),
            critical_alerts_count=critical_count,
            high_risk_count=high_count,
            persistent_sources_count=persistent_count,
            industrial_proximity_count=industrial_count,
            category_breakdown=cat_breakdown
        )

        # Apply optional minimum risk level filtering
        if min_risk_level:
            rank_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
            target_rank = rank_map.get(min_risk_level.upper(), 1)
            decision_anomalies = [
                item for item in decision_anomalies
                if rank_map.get(item.risk_assessment.risk_level.value, 1) >= target_rank
            ]

        logger.info(f"Decision Intelligence pipeline execution complete: {summary.total_anomalies} total events, {summary.critical_alerts_count} CRITICAL alerts.")

        return DecisionIntelligenceResponse(
            status="success",
            source=enriched_res.source,
            timestamp=datetime.now().isoformat(),
            summary=summary,
            data=decision_anomalies
        )

    async def get_active_alerts(
        self,
        days: int = settings.FIRMS_DEFAULT_DAYS,
        source: str = settings.FIRMS_DEFAULT_SOURCE,
        country: str = settings.FIRMS_DEFAULT_COUNTRY,
        use_cache: bool = True,
        use_live_osm: bool = True
    ) -> DecisionIntelligenceResponse:
        """Helper returning only active CRITICAL and HIGH risk monitoring alerts."""
        return await self.get_decision_intelligence(
            days=days,
            source=source,
            country=country,
            use_cache=use_cache,
            use_live_osm=use_live_osm,
            min_risk_level="HIGH"
        )

risk_service = RiskService()
