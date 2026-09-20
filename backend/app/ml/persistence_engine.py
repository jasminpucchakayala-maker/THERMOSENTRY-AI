import math
import hashlib
from datetime import datetime
from typing import List, Dict, Tuple, Any
from backend.app.models.thermal_classification import ClassifiedThermalAnomaly, EventCategory
from backend.app.models.persistence import (
    PersistenceType,
    PersistenceInfo,
    PersistentThermalAnomaly,
    PersistentCluster
)
from backend.app.config import settings

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two point coordinates in kilometers."""
    R = 6371.0  # Earth's mean radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class PersistenceEngine:
    """Engine for spatial clustering and persistent thermal source identification."""

    def __init__(self, proximity_radius_km: float = settings.PERSISTENCE_DISTANCE_THRESHOLD_KM):
        self.proximity_radius_km = proximity_radius_km
        self.time_window_days = settings.PERSISTENCE_TIME_WINDOW_DAYS

    def _generate_cluster_id(self, lat: float, lon: float) -> str:
        raw = f"{round(lat, 2)}_{round(lon, 2)}"
        return "cluster_" + hashlib.md5(raw.encode("utf-8")).hexdigest()[:10]

    def cluster_anomalies(
        self,
        anomalies: List[ClassifiedThermalAnomaly]
    ) -> List[List[ClassifiedThermalAnomaly]]:
        """Groups anomalies into spatial clusters within the proximity radius."""
        clusters: List[List[ClassifiedThermalAnomaly]] = []

        for anomaly in anomalies:
            assigned = False
            for cluster in clusters:
                # Calculate distance to cluster centroid (first member or mean)
                centroid_lat = sum(a.latitude for a in cluster) / len(cluster)
                centroid_lon = sum(a.longitude for a in cluster) / len(cluster)
                dist = haversine_distance_km(anomaly.latitude, anomaly.longitude, centroid_lat, centroid_lon)

                if dist <= self.proximity_radius_km:
                    cluster.append(anomaly)
                    assigned = True
                    break

            if not assigned:
                clusters.append([anomaly])

        return clusters

    def analyze_clusters(
        self,
        anomalies: List[ClassifiedThermalAnomaly]
    ) -> Tuple[List[PersistentThermalAnomaly], List[PersistentCluster]]:
        """
        Runs spatial clustering and evaluates persistence metrics across all anomaly observations.
        Returns (persistent_anomalies, persistent_clusters).
        """
        raw_clusters = self.cluster_anomalies(anomalies)
        persistent_anomalies: List[PersistentThermalAnomaly] = []
        cluster_summaries: List[PersistentCluster] = []

        for cluster_members in raw_clusters:
            # Sort by acquisition date
            dates = []
            for m in cluster_members:
                try:
                    dates.append(datetime.strptime(m.acquisition_date, "%Y-%m-%d"))
                except ValueError:
                    dates.append(datetime.now())
            dates.sort()

            first_seen_str = dates[0].strftime("%Y-%m-%d")
            last_seen_str = dates[-1].strftime("%Y-%m-%d")
            duration_days = (dates[-1] - dates[0]).days

            if duration_days > self.time_window_days:
                continue

            obs_count = len(cluster_members)

            # Spatial centroid
            centroid_lat = round(sum(m.latitude for m in cluster_members) / obs_count, 4)
            centroid_lon = round(sum(m.longitude for m in cluster_members) / obs_count, 4)
            cluster_id = self._generate_cluster_id(centroid_lat, centroid_lon)

            # Calculate persistence score
            # Base logic: observation count + temporal duration
            base_score = 0.25 * obs_count + 0.15 * min(duration_days, 5)

            # Extra weight if classified as Industrial Flare (gas flares stay fixed at plant stacks)
            has_flare = any(m.classification.category == EventCategory.INDUSTRIAL_FLARE for m in cluster_members)
            if has_flare:
                base_score += 0.35

            persistence_score = round(min(1.0, max(0.15, base_score)), 2)

            is_persistent = persistence_score >= 0.50 or obs_count >= 3 or has_flare

            if persistence_score >= 0.65:
                p_type = PersistenceType.HIGHLY_PERSISTENT_INDUSTRIAL
                desc = f"Highly persistent thermal source identified across {obs_count} observation(s) over {duration_days} day(s). High probability of industrial infrastructure."
            elif 0.40 <= persistence_score < 0.65:
                p_type = PersistenceType.RECURRING_SEASONAL
                desc = f"Recurring thermal activity detected ({obs_count} observations). Consistent with seasonal agricultural or localized burning."
            else:
                p_type = PersistenceType.TRANSIENT_EVENT
                desc = f"Single or short-duration transient thermal event ({obs_count} observation)."

            p_info = PersistenceInfo(
                cluster_id=cluster_id,
                is_persistent=is_persistent,
                persistence_score=persistence_score,
                persistence_type=p_type,
                observation_count=obs_count,
                first_seen=first_seen_str,
                last_seen=last_seen_str,
                duration_days=duration_days,
                radius_km=self.proximity_radius_km,
                description=desc
            )

            # Build enriched PersistentThermalAnomaly list
            for m in cluster_members:
                p_anomaly = PersistentThermalAnomaly(
                    **m.model_dump(),
                    persistence=p_info
                )
                persistent_anomalies.append(p_anomaly)

            # Calculate summary physical metrics
            frps = [m.frp for m in cluster_members if m.frp is not None]
            temps = [m.brightness_temperature for m in cluster_members if m.brightness_temperature is not None]

            avg_frp = round(sum(frps) / len(frps), 1) if frps else 0.0
            max_temp = round(max(temps), 1) if temps else 0.0

            cluster_summaries.append(PersistentCluster(
                cluster_id=cluster_id,
                centroid_latitude=centroid_lat,
                centroid_longitude=centroid_lon,
                observation_count=obs_count,
                is_persistent=is_persistent,
                persistence_score=persistence_score,
                persistence_type=p_type,
                first_seen=first_seen_str,
                last_seen=last_seen_str,
                avg_frp=avg_frp,
                max_brightness=max_temp
            ))

        return persistent_anomalies, cluster_summaries

persistence_engine = PersistenceEngine()
