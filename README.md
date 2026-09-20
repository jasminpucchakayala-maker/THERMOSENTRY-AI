# THERMOSENTRY AI — Satellite Thermal Intelligence

**THERMOSENTRY AI** is an AI-powered satellite-to-decision intelligence system designed to transform raw satellite thermal anomaly observations into actionable risk and industrial intelligence.

---

## Core Pipeline Architecture

```text
NASA FIRMS
    ↓
Thermal Anomaly Data (Ingestion)
    ↓
Validation & Normalization Layer
    ↓
Backend Data API (FastAPI)
    ↓
Future AI / Risk Pipeline (Classification → Persistence → OSM Context → Risk Engine)
```

---

## Key Features (STEP 1 Foundation)

* **NASA FIRMS Integration**: Native client for NASA Active Fire / Thermal Anomaly CSV web APIs.
* **Strict Validation & Cleaning**: Validates coordinates (WGS84 lat [-90, 90], lon [-180, 180]), parses numeric metrics, normalizes dates to ISO standard, and filters invalid/malformed records with detailed diagnostic logging.
* **Spatial-Temporal Deduplication**: Generates unique SHA-256 composite IDs based on location, date, time, and satellite platform to eliminate duplicate satellite passes.
* **Resilient Offline Caching & Fallback**: Stores raw FIRMS responses (`backend/data/raw/`) and processed datasets (`backend/data/processed/`). Gracefully falls back to local cached data or built-in sample data when an API key is missing or the external API is unavailable.
* **FastAPI Backend Endpoints**: Standardized REST endpoints returning structured JSON data.

---

## Requirements

* **OS**: Windows 11 (PowerShell)
* **Python**: Python 3.10+ (Tested on Python 3.14)
* **NASA FIRMS API Key**: (Optional for development, required for live NASA data). Obtain a free `MAP_KEY` at [https://firms.modaps.eosdis.nasa.gov/api/map_key/](https://firms.modaps.eosdis.nasa.gov/api/map_key/).

---

## Installation (Windows PowerShell)

```powershell
# 1. Clone or open the project folder
cd c:\Users\jasmi\OneDrive\Desktop\THERMOSENTRY-AI

# 2. Create Python virtual environment
python -m venv .venv

# 3. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Install backend dependencies
pip install -r requirements.txt
```

---

## Configuration

Copy the sample environment file `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Edit `.env` to supply your NASA FIRMS `MAP_KEY`:

```env
FIRMS_API_KEY=your_actual_firms_map_key_here
FIRMS_BASE_URL=https://firms.modaps.eosdis.nasa.gov/api/
FIRMS_DEFAULT_SOURCE=VIIRS_SNPP_NRT
FIRMS_DEFAULT_DAYS=1
FIRMS_DEFAULT_COUNTRY=IND
```

> **Note**: If `FIRMS_API_KEY` is left blank, the system automatically runs in **Offline Sample Mode** using local datasets.

---

## Running the Backend Server

Start the FastAPI application with Uvicorn:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000
```

Access interactive API docs at:
* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Running Automated Tests

Run the backend test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests
```

---

## API Documentation

### 1. Health Check
* **Endpoint**: `GET /api/health`
* **Description**: Returns operational status and API key configuration state.
* **Sample Response**:
  ```json
  {
    "status": "healthy",
    "service": "THERMOSENTRY AI",
    "environment": "development",
    "firms_configured": false
  }
  ```

## Backend Intelligence APIs

The backend preserves the live FIRMS endpoint and exposes the staged intelligence pipeline:

- `GET /api/classified-anomalies` - baseline rule-based classification with evidence and method metadata.
- `GET /api/persistent-anomalies` and `GET /api/persistent-clusters` - configurable spatial-temporal persistence analysis.
- `GET /api/enriched-anomalies` and `GET /api/nearby-industrial` - OpenStreetMap/Overpass industrial context, with transparent offline cache fallback.
- `GET /api/decision-intelligence` - combined classification, persistence, OSM, and explainable risk output.
- `GET /api/classification/{event_id}`, `/api/persistence/{event_id}`, `/api/industrial-context/{event_id}`, `/api/risk/{event_id}`, `/api/decision/{event_id}` - event-level views.
- `POST /api/decision/analyze` - accepts `{ "event_id": "..." }` or `{ "anomaly": { ... } }`.
- `GET /api/reports/{event_id}` - downloads an HTML report generated from the analyzed event.

Classification is explicitly labeled `baseline`; it is not a trained ML model. Exposure and vulnerability remain unavailable unless backed by measured data. Configure timeouts, persistence thresholds, OSM radius, and risk weights through environment variables described in `.env.example`.

### 2. Thermal Anomalies Ingestion
* **Endpoint**: `GET /api/thermal-anomalies`
* **Query Parameters**:
  * `days` (int, default=1): Number of historical days to fetch (1-10)
  * `source` (str, default="VIIRS_SNPP_NRT"): FIRMS product source (`VIIRS_SNPP_NRT`, `VIIRS_NOAA20_NRT`, `VIIRS_NOAA21_NRT`, `MODIS_NRT`)
  * `country` (str, default="IND"): ISO3 country code
  * `use_cache` (bool, default=true): Allow fallback to local cache/sample data if offline
* **Sample Response**:
  ```json
  {
    "status": "success",
    "count": 10,
    "source": "NASA FIRMS (Offline Sample Data)",
    "timestamp": "2026-09-13T21:00:00",
    "data": [
      {
        "id": "a1b2c3d4e5f67890",
        "latitude": 16.5062,
        "longitude": 80.6480,
        "acquisition_date": "2026-09-12",
        "acquisition_time": "1230",
        "satellite": "VIIRS",
        "instrument": "VIIRS",
        "confidence": 60.0,
        "brightness_temperature": 341.2,
        "frp": 48.7,
        "day_night": "D",
        "source": "NASA FIRMS"
      }
    ]
  }
  ```
