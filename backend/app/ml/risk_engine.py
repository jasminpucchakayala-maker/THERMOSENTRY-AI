from typing import Dict, Any, Tuple
from backend.app.models.osm_context import EnrichedThermalAnomaly
from backend.app.models.thermal_classification import EventCategory
from backend.app.models.decision_intelligence import (
    RiskLevel,
    RiskAssessment,
    DecisionIntelligenceAnomaly
)
from backend.app.config import settings

class ExplainableRiskEngine:
    """Multi-factor risk assessment engine calculating composite risk scores and operational recommendations."""

    def evaluate_risk(self, anomaly: EnrichedThermalAnomaly) -> RiskAssessment:
        """
        Evaluates physical metrics, AI classification, persistence, and OSM industrial context 
        to calculate a composite risk score (0-100), risk rating, and actionable recommendation.
        """
        frp = float(anomaly.frp) if anomaly.frp is not None else 0.0
        brightness = float(anomaly.brightness_temperature) if anomaly.brightness_temperature is not None else 300.0
        confidence = float(anomaly.confidence) if anomaly.confidence is not None else None

        category = anomaly.classification.category
        p_info = anomaly.persistence
        osm_info = anomaly.industrial_context

        # 1. Base Physical Risk Contribution (0 to 65 points)
        frp_pts = min(40.0, (frp / 100.0) * 40.0)
        temp_delta = max(0.0, brightness - 298.15)
        temp_pts = min(25.0, (temp_delta / 80.0) * 25.0)
        base_physical = frp_pts + temp_pts

        # 2. Classification Category Weighting
        cat_weights = {
            EventCategory.WILDFIRE: 1.25,
            EventCategory.VOLCANIC_ACTIVITY: 1.40,
            EventCategory.URBAN_LANDFILL: 1.15,
            EventCategory.INDUSTRIAL_FLARE: 1.20 if osm_info.has_nearby_industrial else 0.90,
            EventCategory.AGRICULTURAL_BURNING: 0.75,
            EventCategory.SOLAR_GLINT_NOISE: 0.20
        }
        cat_weight = cat_weights.get(category, 1.0)

        # 3. Persistence Index Contribution
        persistence_factor = 1.0 + (p_info.persistence_score * 0.25)

        # 4. OSM Industrial Risk Multiplier
        industrial_modifier = osm_info.risk_modifier

        # 5. Composite Risk Score Calculation
        available_weights = settings.RISK_WEIGHT_THERMAL_INTENSITY + settings.RISK_WEIGHT_PERSISTENCE + settings.RISK_WEIGHT_INDUSTRIAL_PROXIMITY
        if confidence is not None:
            available_weights += settings.RISK_WEIGHT_CONFIDENCE
        confidence_factor = (confidence / 100.0) if confidence is not None else None
        thermal_factor = min(1.0, base_physical / 65.0)
        persistence_factor_score = p_info.persistence_score
        industrial_factor = min(1.0, max(0.0, (industrial_modifier - 1.0) / 1.5))
        weighted_score = (
            thermal_factor * settings.RISK_WEIGHT_THERMAL_INTENSITY
            + persistence_factor_score * settings.RISK_WEIGHT_PERSISTENCE
            + industrial_factor * settings.RISK_WEIGHT_INDUSTRIAL_PROXIMITY
            + (confidence_factor or 0.0) * settings.RISK_WEIGHT_CONFIDENCE
        ) / max(available_weights, 1.0)
        raw_score = weighted_score * 100.0 * cat_weight * persistence_factor * industrial_modifier
        composite_score = round(min(100.0, max(5.0, raw_score)), 1)

        # 6. Assign Risk Level
        if composite_score >= 80.0:
            level = RiskLevel.CRITICAL
        elif composite_score >= 60.0:
            level = RiskLevel.HIGH
        elif composite_score >= 35.0:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        # 7. Generate Actionable Operational Recommendation
        if level == RiskLevel.CRITICAL:
            if osm_info.has_nearby_industrial and osm_info.nearest_facility_name:
                rec = f"CRITICAL INDUSTRIAL THREAT: Dispatch Emergency Response Team immediately to {osm_info.nearest_facility_name}. Establish 3km hazardous isolation perimeter."
            else:
                rec = "CRITICAL WILDFIRE EMERGENCY: Deploy heavy aerial suppression assets immediately. Initiate community evacuation and wildfire containment protocol."
        elif level == RiskLevel.HIGH:
            if osm_info.has_nearby_industrial:
                rec = f"HIGH RISK ALERT: Priority dispatch to investigate thermal anomaly near {osm_info.nearest_facility_name or 'industrial zone'}. Alert facility safety control."
            else:
                rec = "HIGH RISK WILDFIRE ALERT: Deploy ground fire response unit. Establish fire lines and monitor wind dispersion."
        elif level == RiskLevel.MEDIUM:
            rec = "MODERATE RISK ADVISORY: Continue automated satellite tracking over subsequent orbits. Log event with regional fire authorities."
        else:
            rec = "LOW RISK ROUTINE: Normal background satellite observation. Standard log recording only."

        # 8. Factor Breakdown & Explanation
        factors = {
            "base_physical_score": round(base_physical, 1),
            "category_weight": cat_weight,
            "persistence_factor": round(persistence_factor, 2),
            "industrial_risk_modifier": industrial_modifier,
            "confidence": confidence if confidence is not None else None,
            "exposure": {"available": False, "value": None},
            "vulnerability": {"available": bool(osm_info.has_nearby_industrial), "value": industrial_factor if osm_info.has_nearby_industrial else None},
        }

        reasons = [
            f"Physical intensity score of {round(base_physical, 1)} pts (FRP: {frp} MW, Brightness: {brightness}K)."
        ]
        if osm_info.has_nearby_industrial and osm_info.nearest_facility_name:
            reasons.append(f"Located {osm_info.distance_to_nearest_km} km from {osm_info.nearest_facility_name} ({osm_info.nearest_facility_type}), elevating vulnerability ({industrial_modifier}x risk modifier).")
        if p_info.is_persistent:
            reasons.append(f"Identified as persistent thermal source across {p_info.observation_count} historical observations.")

        explanation_str = f"Assessed as {level.value} Risk ({composite_score}/100). " + " ".join(reasons)

        return RiskAssessment(
            composite_risk_score=composite_score,
            risk_level=level,
            action_recommendation=rec,
            risk_factors=factors,
            explanation=explanation_str,
            factors={
                "thermal_intensity": {"available": True, "value": round(thermal_factor, 3)},
                "persistence": {"available": True, "value": round(persistence_factor_score, 3)},
                "industrial_proximity": {"available": True, "value": round(industrial_factor, 3)},
                "confidence": {"available": confidence is not None, "value": confidence_factor},
                "exposure": {"available": False, "value": None},
                "vulnerability": {"available": bool(osm_info.has_nearby_industrial), "value": industrial_factor if osm_info.has_nearby_industrial else None},
            }
        )

    def evaluate_decision_anomaly(self, anomaly: EnrichedThermalAnomaly) -> DecisionIntelligenceAnomaly:
        """Helper evaluating an EnrichedThermalAnomaly into a full DecisionIntelligenceAnomaly."""
        assessment = self.evaluate_risk(anomaly)
        return DecisionIntelligenceAnomaly(
            **anomaly.model_dump(),
            risk_assessment=assessment
        )

risk_engine = ExplainableRiskEngine()
