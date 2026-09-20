from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.thermal_anomaly import ThermalAnomaly
from backend.app.models.decision_intelligence import RiskLevel
from backend.app.ml.classifier import classifier
from backend.app.ml.persistence_engine import persistence_engine
from backend.app.ml.osm_engine import osm_engine
from backend.app.ml.risk_engine import risk_engine
from backend.app.models.osm_context import EnrichedThermalAnomaly

client = TestClient(app)

def test_risk_engine_critical_industrial_scenario():
    raw = ThermalAnomaly(
        id="risk_test_01",
        latitude=16.5062,
        longitude=80.6480,
        acquisition_date="2026-09-12",
        acquisition_time="1230",
        satellite="VIIRS",
        instrument="VIIRS",
        confidence=95.0,
        brightness_temperature=360.0,
        frp=90.0,
        day_night="N",
        source="Test"
    )
    classified = classifier.classify_classified_anomaly(raw)
    persistent, _ = persistence_engine.analyze_clusters([classified])
    
    # Manually load Visakha Refinery context
    ctx = asyncio_run_ctx(16.5062, 80.6480)
    
    enriched = EnrichedThermalAnomaly(
        **persistent[0].model_dump(),
        industrial_context=ctx
    )

    assessment = risk_engine.evaluate_risk(enriched)
    assert assessment.composite_risk_score >= 75.0
    assert assessment.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]
    assert "Visakha Refinery" in assessment.action_recommendation or "Industrial" in assessment.action_recommendation

def asyncio_run_ctx(lat, lon):
    import asyncio
    return asyncio.run(osm_engine.get_industrial_context(lat, lon, use_live=False))

def test_get_decision_intelligence_endpoint():
    response = client.get("/api/decision-intelligence?use_live_osm=false")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "summary" in data
    assert data["summary"]["total_anomalies"] > 0
    assert "category_breakdown" in data["summary"]
    first = data["data"][0]
    assert "risk_assessment" in first
    assert "composite_risk_score" in first["risk_assessment"]
    assert "action_recommendation" in first["risk_assessment"]

def test_get_active_alerts_endpoint():
    response = client.get("/api/alerts?use_live_osm=false")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "summary" in data

def test_post_analyze_event_endpoint():
    # Fetch sample enriched anomaly to pass to analyze-event
    res = client.get("/api/enriched-anomalies?use_live_osm=false").json()
    sample_enriched = res["data"][0]

    response = client.post("/api/analyze-event", json=sample_enriched)
    assert response.status_code == 200
    data = response.json()
    assert "risk_assessment" in data
    assert data["risk_assessment"]["composite_risk_score"] >= 0.0
