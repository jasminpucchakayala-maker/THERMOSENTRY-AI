from datetime import datetime

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.ml.classifier import classifier
from backend.app.ml.persistence_engine import persistence_engine
from backend.app.ml.risk_engine import risk_engine
from backend.app.models.osm_context import EnrichedThermalAnomaly, OSMIndustrialContext
from backend.app.models.persistence import PersistenceInfo, PersistenceType
from backend.app.models.thermal_anomaly import ThermalAnomaly
from backend.app.services.report_service import report_service

client = TestClient(app)


def sample_anomaly():
    return ThermalAnomaly(
        id="firms-record-1",
        firms_id="NASA-123",
        event_id="TH-ABC123",
        latitude=16.5062,
        longitude=80.6480,
        acquisition_date="2026-09-20",
        acquisition_time="1230",
        satellite="NOAA-20",
        instrument="VIIRS",
        confidence=90.0,
        brightness_temperature=350.0,
        frp=40.0,
        day_night="D",
        source="NASA FIRMS (Live)",
    )


def test_normalized_anomaly_preserves_source_and_internal_ids():
    anomaly = sample_anomaly()
    assert anomaly.firms_id == "NASA-123"
    assert anomaly.event_id == "TH-ABC123"


def test_baseline_classification_is_transparent():
    result = classifier.classify(sample_anomaly())
    assert result.method == "baseline"
    assert result.evidence
    assert result.class_name
    assert result.reasoning


def test_report_contains_real_pipeline_sections():
    classified = classifier.classify_classified_anomaly(sample_anomaly())
    persistent, _ = persistence_engine.analyze_clusters([classified])
    enriched = EnrichedThermalAnomaly(
        **persistent[0].model_dump(),
        industrial_context=OSMIndustrialContext(
            has_nearby_industrial=False,
            source="OpenStreetMap / Overpass (No facility found)",
        ),
    )
    decision = risk_engine.evaluate_decision_anomaly(enriched)
    html = report_service.render_html(decision)
    assert "THERMOSENTRY AI" in html
    assert "NASA-123" in html
    assert "Classification" in html
    assert "Persistence" in html
    assert "Industrial Context" in html
    assert "Risk" in html


def test_unknown_event_id_returns_404():
    response = client.get("/api/decision/does-not-exist")
    assert response.status_code == 404
