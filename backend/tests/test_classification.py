from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.thermal_anomaly import ThermalAnomaly
from backend.app.models.thermal_classification import EventCategory, SeverityLevel
from backend.app.ml.classifier import classify_anomaly, ThermalClassifier

client = TestClient(app)

def test_classify_wildfire_profile():
    anomaly = ThermalAnomaly(
        id="wildfire_test_01",
        latitude=16.50,
        longitude=80.64,
        acquisition_date="2026-09-12",
        acquisition_time="1230",
        satellite="VIIRS",
        instrument="VIIRS",
        confidence=95.0,
        brightness_temperature=365.0,
        frp=110.0,
        day_night="D",
        source="Test"
    )
    result = classify_anomaly(anomaly)
    assert result.category == EventCategory.WILDFIRE
    assert result.severity_level == SeverityLevel.CRITICAL
    assert result.confidence_score >= 0.70
    assert "High Fire Radiative Power" in result.explanation

def test_classify_industrial_flare_profile():
    anomaly = ThermalAnomaly(
        id="flare_test_01",
        latitude=21.14,
        longitude=79.08,
        acquisition_date="2026-09-12",
        acquisition_time="2215",
        satellite="VIIRS",
        instrument="VIIRS",
        confidence=85.0,
        brightness_temperature=348.0,
        frp=35.0,
        day_night="N",  # Nighttime detection
        source="Test"
    )
    result = classify_anomaly(anomaly)
    assert result.category == EventCategory.INDUSTRIAL_FLARE
    assert result.severity_level in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]
    assert "Nighttime thermal signature" in result.explanation

def test_classify_agricultural_burn_profile():
    anomaly = ThermalAnomaly(
        id="agri_test_01",
        latitude=28.70,
        longitude=77.10,
        acquisition_date="2026-09-12",
        acquisition_time="1140",
        satellite="N20",
        instrument="VIIRS",
        confidence=65.0,
        brightness_temperature=325.0,
        frp=20.0,
        day_night="D",
        source="Test"
    )
    result = classify_anomaly(anomaly)
    assert result.category == EventCategory.AGRICULTURAL_BURNING
    assert result.severity_level in [SeverityLevel.MEDIUM, SeverityLevel.LOW]

def test_classify_solar_glint_profile():
    anomaly = ThermalAnomaly(
        id="glint_test_01",
        latitude=12.97,
        longitude=77.59,
        acquisition_date="2026-09-12",
        acquisition_time="1300",
        satellite="VIIRS",
        instrument="VIIRS",
        confidence=25.0, # Low confidence
        brightness_temperature=302.0,
        frp=2.0,
        day_night="D",
        source="Test"
    )
    result = classify_anomaly(anomaly)
    assert result.category == EventCategory.SOLAR_GLINT_NOISE
    assert result.severity_level == SeverityLevel.LOW

def test_get_classified_anomalies_endpoint():
    response = client.get("/api/classified-anomalies")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] > 0
    first = data["data"][0]
    assert "classification" in first
    assert "category" in first["classification"]
    assert "confidence_score" in first["classification"]
    assert "severity_level" in first["classification"]
    assert "explanation" in first["classification"]

def test_post_classify_single_endpoint():
    payload = {
        "id": "single_test_01",
        "latitude": 19.07,
        "longitude": 72.87,
        "acquisition_date": "2026-09-12",
        "acquisition_time": "0310",
        "satellite": "MODIS",
        "instrument": "MODIS",
        "confidence": 95.0,
        "brightness_temperature": 362.1,
        "frp": 110.5,
        "day_night": "N",
        "source": "Test Payload"
    }
    response = client.post("/api/classify-single", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "single_test_01"
    assert "classification" in data
    assert data["classification"]["category"] is not None
