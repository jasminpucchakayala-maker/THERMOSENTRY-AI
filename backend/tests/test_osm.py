import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.ml.osm_engine import osm_engine

client = TestClient(app)

def test_osm_local_sample_lookup():
    # Test coordinates near Visakha Refinery (16.5062, 80.6480)
    ctx = asyncio.run(osm_engine.get_industrial_context(16.5062, 80.6480, use_live=False))
    assert ctx.has_nearby_industrial is True
    assert ctx.nearest_facility_name is not None
    assert "Visakha Refinery" in ctx.nearest_facility_name
    assert ctx.distance_to_nearest_km is not None and ctx.distance_to_nearest_km <= 1.0
    assert ctx.risk_modifier >= 1.5

def test_risk_modifier_calculation():
    facilities = osm_engine.load_local_sample_facilities(16.5062, 80.6480)
    modifier = osm_engine.calculate_risk_modifier(facilities)
    assert modifier >= 1.5

def test_get_nearby_industrial_endpoint():
    response = client.get("/api/nearby-industrial?lat=16.5062&lon=80.6480&use_live=false")
    assert response.status_code == 200
    data = response.json()
    assert data["has_nearby_industrial"] is True
    assert data["nearest_facility_name"] is not None
    assert data["risk_modifier"] >= 1.5

def test_get_enriched_anomalies_endpoint():
    response = client.get("/api/enriched-anomalies?use_live_osm=false")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] > 0
    assert "industrial_proximity_count" in data
    first = data["data"][0]
    assert "industrial_context" in first
    assert "has_nearby_industrial" in first["industrial_context"]
    assert "risk_modifier" in first["industrial_context"]
