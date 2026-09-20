from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.thermal_anomaly import ThermalAnomaly
from backend.app.models.thermal_classification import EventCategory
from backend.app.models.persistence import PersistenceType
from backend.app.ml.classifier import classifier
from backend.app.ml.persistence_engine import persistence_engine, haversine_distance_km

client = TestClient(app)

def test_haversine_distance():
    # Distance between two nearby Vijayawada coordinates (~0.72 km)
    dist = haversine_distance_km(16.5062, 80.6480, 16.5120, 80.6510)
    assert 0.5 <= dist <= 1.0

def test_spatial_clustering_and_persistence():
    # Create 3 nearby detections over 3 days (industrial/persistent cluster profile)
    raw1 = ThermalAnomaly(
        id="p1", latitude=16.5062, longitude=80.6480,
        acquisition_date="2026-09-10", acquisition_time="1230",
        satellite="VIIRS", instrument="VIIRS", confidence=90, brightness_temperature=355.0, frp=80.0, day_night="N", source="test"
    )
    raw2 = ThermalAnomaly(
        id="p2", latitude=16.5070, longitude=80.6485,
        acquisition_date="2026-09-11", acquisition_time="1230",
        satellite="N20", instrument="VIIRS", confidence=90, brightness_temperature=358.0, frp=85.0, day_night="N", source="test"
    )
    raw3 = ThermalAnomaly(
        id="p3", latitude=16.5065, longitude=80.6482,
        acquisition_date="2026-09-12", acquisition_time="1230",
        satellite="N21", instrument="VIIRS", confidence=90, brightness_temperature=360.0, frp=90.0, day_night="N", source="test"
    )

    classified = [classifier.classify_classified_anomaly(a) for a in [raw1, raw2, raw3]]
    persistent_anomalies, clusters = persistence_engine.analyze_clusters(classified)

    assert len(clusters) == 1
    assert len(persistent_anomalies) == 3
    c = clusters[0]
    assert c.observation_count == 3
    assert c.is_persistent is True
    assert c.persistence_score >= 0.70
    assert c.persistence_type == PersistenceType.HIGHLY_PERSISTENT_INDUSTRIAL

def test_transient_event_attribution():
    raw_single = ThermalAnomaly(
        id="t1", latitude=28.7041, longitude=77.1025,
        acquisition_date="2026-09-12", acquisition_time="0740",
        satellite="N20", instrument="VIIRS", confidence=60, brightness_temperature=334.6, frp=31.8, day_night="D", source="test"
    )
    classified = [classifier.classify_classified_anomaly(raw_single)]
    persistent_anomalies, clusters = persistence_engine.analyze_clusters(classified)

    assert len(persistent_anomalies) == 1
    info = persistent_anomalies[0].persistence
    assert info.observation_count == 1
    assert info.persistence_type == PersistenceType.TRANSIENT_EVENT

def test_get_persistent_anomalies_endpoint():
    response = client.get("/api/persistent-anomalies")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] > 0
    assert "persistent_count" in data
    first = data["data"][0]
    assert "persistence" in first
    assert "is_persistent" in first["persistence"]
    assert "persistence_score" in first["persistence"]
    assert "persistence_type" in first["persistence"]

def test_get_persistent_clusters_endpoint():
    response = client.get("/api/persistent-clusters")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "clusters" in data
    assert len(data["clusters"]) == data["count"]

def test_post_analyze_persistence_endpoint():
    raw = ThermalAnomaly(
        id="post_p1", latitude=19.0760, longitude=72.8777,
        acquisition_date="2026-09-12", acquisition_time="0310",
        satellite="MODIS", instrument="MODIS", confidence=95, brightness_temperature=362.1, frp=110.5, day_night="N", source="test"
    )
    classified = classifier.classify_classified_anomaly(raw)
    payload = [classified.model_dump()]

    response = client.post("/api/analyze-persistence", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert "persistence" in data[0]
