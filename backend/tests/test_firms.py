import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.thermal_anomaly import ThermalAnomaly
from backend.app.utils.validation import clean_and_normalize_record, process_and_deduplicate_records
from backend.app.services.firms_service import firms_service

client = TestClient(app)

def test_clean_and_normalize_valid_record():
    raw = {
        "latitude": "16.5062",
        "longitude": "80.6480",
        "acq_date": "2026-09-12",
        "acq_time": "1230",
        "satellite": "VIIRS",
        "instrument": "VIIRS",
        "confidence": "h",
        "bright_ti4": "341.2",
        "frp": "48.7",
        "daynight": "D"
    }
    anomaly, err = clean_and_normalize_record(raw, source_name="Test")
    assert err is None
    assert isinstance(anomaly, ThermalAnomaly)
    assert anomaly.latitude == 16.5062
    assert anomaly.longitude == 80.6480
    assert anomaly.acquisition_date == "2026-09-12"
    assert anomaly.acquisition_time == "1230"
    assert anomaly.satellite == "VIIRS"
    assert anomaly.confidence == 90.0
    assert anomaly.brightness_temperature == 341.2
    assert anomaly.frp == 48.7
    assert anomaly.day_night == "D"

def test_reject_invalid_latitude():
    raw = {"latitude": "95.000", "longitude": "80.6480", "acq_date": "2026-09-12"}
    anomaly, err = clean_and_normalize_record(raw)
    assert anomaly is None
    assert "Invalid latitude" in err

def test_reject_invalid_longitude():
    raw = {"latitude": "16.5062", "longitude": "-185.000", "acq_date": "2026-09-12"}
    anomaly, err = clean_and_normalize_record(raw)
    assert anomaly is None
    assert "Invalid longitude" in err

def test_handle_missing_optional_values():
    raw = {
        "latitude": "21.1458",
        "longitude": "79.0882",
        "acq_date": "2026-09-12",
        "satellite": "N20"
    }
    anomaly, err = clean_and_normalize_record(raw)
    assert err is None
    assert anomaly.confidence is None
    assert anomaly.brightness_temperature is None
    assert anomaly.frp is None
    assert anomaly.day_night is None

def test_deduplicate_identical_records():
    raw_records = [
        {"latitude": "16.5062", "longitude": "80.6480", "acq_date": "2026-09-12", "acq_time": "1230", "satellite": "VIIRS"},
        {"latitude": "16.5062", "longitude": "80.6480", "acq_date": "2026-09-12", "acq_time": "1230", "satellite": "VIIRS"}, # Duplicate
        {"latitude": "21.1458", "longitude": "79.0882", "acq_date": "2026-09-12", "acq_time": "0815", "satellite": "N20"}
    ]
    valid_anomalies, accepted, rejected = process_and_deduplicate_records(raw_records)
    assert accepted == 2
    assert rejected == 1
    assert len(valid_anomalies) == 2

def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "THERMOSENTRY AI"

def test_thermal_anomalies_endpoint_fallback():
    response = client.get("/api/thermal-anomalies?use_cache=true")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] > 0
    assert len(data["data"]) == data["count"]
    first = data["data"][0]
    assert "latitude" in first
    assert "longitude" in first
    assert "acquisition_date" in first
    assert "satellite" in first

import asyncio

def test_firms_service_offline_fallback():
    # Test service method with explicit offline cache request
    response = asyncio.run(firms_service.get_thermal_anomalies(use_cache=True))
    assert response.status == "success"
    assert response.count > 0
    assert "NASA FIRMS" in response.source
