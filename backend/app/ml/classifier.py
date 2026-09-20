from typing import Dict, Any, Tuple
from backend.app.models.thermal_anomaly import ThermalAnomaly
from backend.app.models.thermal_classification import (
    EventCategory,
    SeverityLevel,
    ThermalClassification,
    ClassifiedThermalAnomaly
)

class ThermalClassifier:
    """AI Classification Engine evaluating thermal anomalies into operational event classes."""

    @staticmethod
    def extract_features(anomaly: ThermalAnomaly) -> Dict[str, float]:
        """Derives normalized numerical features from spatial-temporal thermal anomaly attributes."""
        frp = float(anomaly.frp) if anomaly.frp is not None else 0.0
        brightness = float(anomaly.brightness_temperature) if anomaly.brightness_temperature is not None else 300.0
        confidence = float(anomaly.confidence) if anomaly.confidence is not None else 50.0

        # Ambient baseline temperature estimated at ~298.15 K (25°C)
        temp_delta = max(0.0, brightness - 298.15)
        frp_temp_ratio = round(frp / (temp_delta + 1.0), 4)
        is_nighttime = 1.0 if anomaly.day_night == "N" else 0.0
        intensity_index = round((frp * (confidence / 100.0)), 2)

        return {
            "frp": round(frp, 2),
            "brightness_temperature": round(brightness, 1),
            "confidence": round(confidence, 1),
            "temp_delta_above_ambient": round(temp_delta, 1),
            "frp_temp_ratio": frp_temp_ratio,
            "is_nighttime": is_nighttime,
            "intensity_index": intensity_index
        }

    def classify(self, anomaly: ThermalAnomaly) -> ThermalClassification:
        """Classifies a ThermalAnomaly into an EventCategory with confidence and severity."""
        feats = self.extract_features(anomaly)
        frp = feats["frp"]
        brightness = feats["brightness_temperature"]
        confidence = feats["confidence"]
        temp_delta = feats["temp_delta_above_ambient"]
        is_night = feats["is_nighttime"] == 1.0

        # Category score dictionary
        scores = {
            EventCategory.WILDFIRE: 0.1,
            EventCategory.INDUSTRIAL_FLARE: 0.1,
            EventCategory.AGRICULTURAL_BURNING: 0.1,
            EventCategory.URBAN_LANDFILL: 0.1,
            EventCategory.VOLCANIC_ACTIVITY: 0.05,
            EventCategory.SOLAR_GLINT_NOISE: 0.05
        }

        reasons = []

        # 1. Check for Solar Glint / Noise
        if confidence < 40.0 or (frp < 5.0 and temp_delta < 15.0):
            scores[EventCategory.SOLAR_GLINT_NOISE] += 0.7
            reasons.append("Low detection confidence (<40%) or minimal thermal radiative output (<5 MW)")
        
        # 2. Check for Volcanic Activity
        if brightness >= 380.0 or frp >= 300.0:
            scores[EventCategory.VOLCANIC_ACTIVITY] += 0.8
            reasons.append(f"Extreme thermal emission (Brightness {brightness}K, FRP {frp} MW)")

        # 3. Check for Wildfire / High-Intensity Vegetation Fire
        if frp >= 45.0 and brightness >= 335.0 and confidence >= 60.0:
            scores[EventCategory.WILDFIRE] += 0.75
            if frp >= 80.0:
                scores[EventCategory.WILDFIRE] += 0.15
            reasons.append(f"High Fire Radiative Power ({frp} MW) and elevated brightness temperature ({brightness}K)")

        # 4. Check for Industrial Flare / Processing Emission
        if is_night and brightness >= 330.0 and confidence >= 50.0:
            # Nighttime thermal anomalies without massive areal biomass spread strongly indicate industrial flaring/furnaces
            scores[EventCategory.INDUSTRIAL_FLARE] += 0.65
            if frp >= 30.0:
                scores[EventCategory.INDUSTRIAL_FLARE] += 0.15
            reasons.append(f"Nighttime thermal signature (Brightness {brightness}K) characteristic of industrial gas flaring or stack processing")
        elif brightness >= 345.0 and frp < 50.0:
            scores[EventCategory.INDUSTRIAL_FLARE] += 0.4
            reasons.append(f"Intense localized heat ({brightness}K) with moderate FRP ({frp} MW)")

        # 5. Check for Agricultural / Crop Stubble Burning
        if not is_night and 5.0 <= frp <= 45.0 and 310.0 <= brightness <= 340.0:
            scores[EventCategory.AGRICULTURAL_BURNING] += 0.6
            reasons.append(f"Daytime moderate thermal output ({frp} MW, {brightness}K) aligned with open agricultural field burning")

        # 6. Check for Urban / Landfill Fire
        if 10.0 <= frp <= 40.0 and confidence >= 50.0:
            scores[EventCategory.URBAN_LANDFILL] += 0.35

        # Normalize score probabilities
        max_category = max(scores, key=scores.get)
        raw_max_score = scores[max_category]
        total_score = sum(scores.values())
        confidence_score = round(min(0.98, max(0.50, raw_max_score / total_score if total_score > 0 else 0.50)), 2)

        # Assess Severity Level based on category and physical metrics
        if max_category in [EventCategory.WILDFIRE, EventCategory.VOLCANIC_ACTIVITY] and (frp >= 70.0 or brightness >= 350.0):
            severity = SeverityLevel.CRITICAL
        elif max_category in [EventCategory.WILDFIRE, EventCategory.INDUSTRIAL_FLARE] or frp >= 40.0:
            severity = SeverityLevel.HIGH
        elif max_category in [EventCategory.AGRICULTURAL_BURNING, EventCategory.URBAN_LANDFILL] or frp >= 15.0:
            severity = SeverityLevel.MEDIUM
        else:
            severity = SeverityLevel.LOW

        # Format human-readable explanation
        explanation_text = (
            f"Classified as {max_category.value} with {int(confidence_score * 100)}% baseline confidence. "
            + (reasons[0] if reasons else f"Thermal output of {frp} MW and brightness temperature {brightness}K.")
        )

        canonical_names = {
            EventCategory.WILDFIRE: "Vegetation Fire",
            EventCategory.INDUSTRIAL_FLARE: "Gas Flare",
            EventCategory.AGRICULTURAL_BURNING: "Agricultural Burning",
            EventCategory.URBAN_LANDFILL: "Industrial Fire",
            EventCategory.VOLCANIC_ACTIVITY: "Uncertain Anomaly",
            EventCategory.SOLAR_GLINT_NOISE: "Uncertain Anomaly",
        }
        evidence = [
            f"FRP={frp} MW",
            f"brightness_temperature={brightness} K",
            f"confidence={confidence}%",
            f"day_night={anomaly.day_night or 'unknown'}",
        ]
        reasoning = reasons[0] if reasons else f"Thermal output of {frp} MW and brightness temperature {brightness}K."

        return ThermalClassification(
            category=max_category,
            confidence_score=confidence_score,
            severity_level=severity,
            features=feats,
            explanation=explanation_text,
            method="baseline", evidence=evidence, reasoning=reasoning,
            class_name=canonical_names[max_category]
        )

    def classify_classified_anomaly(self, anomaly: ThermalAnomaly) -> ClassifiedThermalAnomaly:
        """Helper that takes a ThermalAnomaly and returns a full ClassifiedThermalAnomaly object."""
        classification = self.classify(anomaly)
        return ClassifiedThermalAnomaly(
            **anomaly.model_dump(),
            classification=classification
        )

# Global classifier instance
classifier = ThermalClassifier()

def classify_anomaly(anomaly: ThermalAnomaly) -> ThermalClassification:
    """Convenience functional wrapper for ThermalClassifier.classify."""
    return classifier.classify(anomaly)
