from datetime import datetime
from typing import List, Optional
from backend.app.config import settings
from backend.app.models.thermal_anomaly import ThermalAnomaly
from backend.app.models.thermal_classification import ClassifiedThermalAnomaly, ClassifiedAnomalyResponse
from backend.app.services.firms_service import firms_service
from backend.app.ml.classifier import classifier
from backend.app.utils.logging_config import logger

class ClassificationService:
    """Service handling batch AI classification of satellite thermal anomalies."""

    def __init__(self):
        self.firms_service = firms_service
        self.classifier = classifier

    def classify_anomalies(self, anomalies: List[ThermalAnomaly]) -> List[ClassifiedThermalAnomaly]:
        """Runs AI classification across a list of ThermalAnomaly records."""
        classified_list = []
        for anomaly in anomalies:
            classified_anomaly = self.classifier.classify_classified_anomaly(anomaly)
            classified_list.append(classified_anomaly)
        
        logger.info(f"Successfully classified {len(classified_list)} thermal anomalies.")
        return classified_list

    async def get_classified_thermal_anomalies(
        self,
        days: int = settings.FIRMS_DEFAULT_DAYS,
        source: str = settings.FIRMS_DEFAULT_SOURCE,
        country: str = settings.FIRMS_DEFAULT_COUNTRY,
        use_cache: bool = True,
        min_severity: Optional[str] = None
    ) -> ClassifiedAnomalyResponse:
        """
        Retrieves thermal anomalies from FIRMSService and runs AI classification over the dataset.
        Optional severity filtering (CRITICAL, HIGH, MEDIUM, LOW).
        """
        firms_response = await self.firms_service.get_thermal_anomalies(
            days=days,
            source=source,
            country=country,
            use_cache=use_cache
        )

        classified_data = self.classify_anomalies(firms_response.data)

        # Apply severity filtering if specified
        if min_severity:
            sev_upper = min_severity.upper()
            severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
            min_rank = severity_order.get(sev_upper, 1)
            classified_data = [
                item for item in classified_data 
                if severity_order.get(item.classification.severity_level.value, 1) >= min_rank
            ]

        return ClassifiedAnomalyResponse(
            status="success",
            count=len(classified_data),
            source=firms_response.source,
            timestamp=datetime.now().isoformat(),
            data=classified_data
        )

classification_service = ClassificationService()
