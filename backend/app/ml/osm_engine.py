import json
import httpx
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from backend.app.config import settings
from backend.app.models.osm_context import IndustrialFacility, OSMIndustrialContext
from backend.app.ml.persistence_engine import haversine_distance_km
from backend.app.utils.logging_config import logger

class OSMEngine:
    """OpenStreetMap spatial engine to query and assess nearby industrial infrastructure."""

    def __init__(self, search_radius_km: float = settings.OSM_SEARCH_RADIUS_KM):
        self.search_radius_km = search_radius_km
        self.sample_file = settings.SAMPLE_DATA_DIR / "osm_industrial_sample.json"
        self.overpass_url = settings.OVERPASS_URL
        self._context_cache: Dict[Tuple[float, float, bool], OSMIndustrialContext] = {}

    async def fetch_live_overpass_facilities(self, lat: float, lon: float) -> Tuple[List[IndustrialFacility], Optional[str]]:
        """Queries OpenStreetMap Overpass API for industrial tags within radius."""
        radius_m = int(self.search_radius_km * 1000)
        overpass_query = f"""
        [out:json][timeout:5];
        (
          node["landuse"="industrial"](around:{radius_m},{lat},{lon});
          way["landuse"="industrial"](around:{radius_m},{lat},{lon});
          node["industrial"](around:{radius_m},{lat},{lon});
          way["industrial"](around:{radius_m},{lat},{lon});
          node["man_made"="works"](around:{radius_m},{lat},{lon});
          way["man_made"="works"](around:{radius_m},{lat},{lon});
          node["power"="plant"](around:{radius_m},{lat},{lon});
          way["power"="plant"](around:{radius_m},{lat},{lon});
        );
        out center 10;
        """
        try:
            async with httpx.AsyncClient(timeout=settings.OSM_TIMEOUT_SECONDS) as client:
                response = await client.post(self.overpass_url, data={"data": overpass_query})

            if response.status_code == 200:
                payload = response.json()
                elements = payload.get("elements", [])
                facilities: List[IndustrialFacility] = []

                for el in elements:
                    tags = el.get("tags", {})
                    name = tags.get("name") or tags.get("operator")
                    ind_type = tags.get("industrial") or tags.get("landuse") or tags.get("power") or "Industrial Zone"
                    
                    # Determine lat/lon from node or way center
                    el_lat = el.get("lat") or el.get("center", {}).get("lat") or lat
                    el_lon = el.get("lon") or el.get("center", {}).get("lon") or lon

                    dist = round(haversine_distance_km(lat, lon, el_lat, el_lon), 2)
                    if dist <= self.search_radius_km:
                        facilities.append(IndustrialFacility(
                            name=name.title() if name else None,
                            type=ind_type.title(),
                            distance_km=dist,
                            latitude=round(el_lat, 4),
                            longitude=round(el_lon, 4),
                            osm_id=f"{el.get('type')}/{el.get('id')}",
                            tags=tags
                        ))

                facilities.sort(key=lambda x: x.distance_km)
                logger.info(f"Overpass API returned {len(facilities)} industrial facilities near ({lat}, {lon})")
                return facilities, None
            else:
                return [], f"Overpass API HTTP {response.status_code}"

        except Exception as e:
            logger.warning(f"Overpass API query failed or timed out: {e}")
            return [], str(e)

    def load_local_sample_facilities(self, lat: float, lon: float) -> List[IndustrialFacility]:
        """Fallback method using local offline sample industrial facility database."""
        if not self.sample_file.exists():
            return []

        try:
            with open(self.sample_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            facilities: List[IndustrialFacility] = []
            for item in data:
                f_lat = item["latitude"]
                f_lon = item["longitude"]
                dist = round(haversine_distance_km(lat, lon, f_lat, f_lon), 2)
                if dist <= self.search_radius_km:
                    facilities.append(IndustrialFacility(
                        name=item["name"],
                        type=item["type"],
                        distance_km=dist,
                        latitude=round(f_lat, 4),
                        longitude=round(f_lon, 4),
                        osm_id=item.get("osm_id"),
                        tags=item.get("tags", {})
                    ))

            facilities.sort(key=lambda x: x.distance_km)
            return facilities
        except Exception as e:
            logger.error(f"Failed to load local industrial database: {e}")
            return []

    def calculate_risk_modifier(self, facilities: List[IndustrialFacility]) -> float:
        """Calculates risk multiplier based on proximity and vulnerability of nearby industrial assets."""
        if not facilities:
            return 1.0

        nearest = facilities[0]
        dist = nearest.distance_km
        f_type = nearest.type.lower()

        modifier = 1.0

        # High-risk hazardous infrastructure (Refineries, Gas/Petroleum Terminals, Chemical Plants)
        if any(keyword in f_type for keyword in ["refinery", "oil", "petroleum", "gas", "chemical"]):
            if dist <= 1.0:
                modifier += 0.80
            elif dist <= 3.0:
                modifier += 0.50
            elif dist <= 5.0:
                modifier += 0.30
        # Moderate-risk infrastructure (Power Plants, Manufacturing, Steelworks)
        elif any(keyword in f_type for keyword in ["power", "steel", "factory", "plant", "works"]):
            if dist <= 1.0:
                modifier += 0.50
            elif dist <= 3.0:
                modifier += 0.30
            elif dist <= 5.0:
                modifier += 0.15
        # General industrial zones
        else:
            if dist <= 2.0:
                modifier += 0.20
            elif dist <= 5.0:
                modifier += 0.10

        return round(min(2.5, modifier), 2)

    async def get_industrial_context(self, lat: float, lon: float, use_live: bool = True) -> OSMIndustrialContext:
        """Evaluates industrial context around coordinates using live Overpass API or local offline fallback."""
        cache_key = (round(lat, 4), round(lon, 4), use_live)
        if cache_key in self._context_cache:
            return self._context_cache[cache_key]
        facilities = []
        source = "OpenStreetMap Overpass API (Live)"

        if use_live:
            facilities, err = await self.fetch_live_overpass_facilities(lat, lon)
            if err or not facilities:
                facilities = self.load_local_sample_facilities(lat, lon)
                source = "OpenStreetMap (Local Infrastructure Cache)" if facilities else "OpenStreetMap / Overpass (No facility found)"
        else:
            facilities = self.load_local_sample_facilities(lat, lon)
            source = "OpenStreetMap (Local Infrastructure Cache)"

        has_nearby = len(facilities) > 0
        nearest_name = facilities[0].name if has_nearby else None
        nearest_type = facilities[0].type if has_nearby else None
        nearest_dist = facilities[0].distance_km if has_nearby else None

        within_3k = sum(1 for f in facilities if f.distance_km <= 3.0)
        within_5k = len(facilities)

        risk_mod = self.calculate_risk_modifier(facilities)

        context = OSMIndustrialContext(
            has_nearby_industrial=has_nearby,
            nearest_facility_name=nearest_name,
            nearest_facility_type=nearest_type,
            distance_to_nearest_km=nearest_dist,
            facilities_within_3km=within_3k,
            facilities_within_5km=within_5k,
            nearby_facilities=facilities,
            risk_modifier=risk_mod,
            source=source
        )
        self._context_cache[cache_key] = context
        return context

osm_engine = OSMEngine()
