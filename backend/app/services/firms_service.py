import csv
import json
import io
import httpx
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from backend.app.config import settings
from backend.app.models.thermal_anomaly import ThermalAnomaly, ThermalAnomalyResponse
from backend.app.utils.validation import process_and_deduplicate_records
from backend.app.utils.logging_config import logger

class FIRMSService:
    """Service to fetch, validate, process, and cache NASA FIRMS thermal anomaly data."""

    def __init__(self):
        self.api_key = settings.FIRMS_API_KEY
        self.base_url = settings.FIRMS_BASE_URL.rstrip("/")
        self.raw_dir = settings.RAW_DATA_DIR
        self.processed_dir = settings.PROCESSED_DATA_DIR
        self.sample_dir = settings.SAMPLE_DATA_DIR

    async def fetch_live_firms_data(self, source: str, country: str, days: int) -> Tuple[Optional[str], Optional[str]]:
        """
        Queries NASA FIRMS API endpoint: /api/country/csv/{MAP_KEY}/{SOURCE}/{COUNTRY}/{DAYS}
        Returns (raw_csv_text, None) on success, or (None, error_message) on failure.
        """
        if not self.api_key:
            return None, "NASA FIRMS API key (FIRMS_API_KEY) is missing. Set it in .env to enable live NASA requests."

        url = f"{self.base_url}/country/csv/{self.api_key}/{source}/{country}/{days}"
        logger.info(f"FIRMS request started: source={source}, country={country}, days={days}")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)

            if response.status_code == 200:
                content = response.text
                if not content or "Invalid MAP_KEY" in content or "Error" in content[:100]:
                    logger.warning("FIRMS API returned invalid response or invalid MAP_KEY.")
                    return None, f"NASA FIRMS API Key rejection or server error: {content[:100].strip()}"

                logger.info(f"FIRMS request completed successfully: Received {len(content)} bytes")
                return content, None
            else:
                response_preview = response.text[:500].strip()
                error_msg = (
                    "NASA FIRMS API HTTP Error: "
                    f"status_code={response.status_code}, "
                    f"response={response_preview}"
                )
                logger.warning(error_msg)
                return None, error_msg

        except httpx.TimeoutException:
            logger.error("FIRMS request timed out after 15 seconds.")
            return None, "NASA FIRMS service timeout."
        except Exception as e:
            logger.error(f"FIRMS request failed due to exception: {str(e)}")
            return None, f"Network or API exception: {str(e)}"

    def parse_csv_string(self, csv_text: str) -> List[Dict[str, Any]]:
        """Parses a CSV text string into a list of dictionaries."""
        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            return [dict(row) for row in reader]
        except Exception as e:
            logger.error(f"Failed to parse CSV payload: {e}")
            return []

    def load_local_sample_data(self) -> Tuple[List[ThermalAnomaly], str]:
        """Fallback method loading built-in sample thermal anomaly dataset."""
        sample_file = self.sample_dir / "firms_sample.csv"
        if not sample_file.exists():
            logger.error(f"Sample dataset file not found at {sample_file}")
            return [], "NASA FIRMS (Sample Data Not Found)"

        logger.info(f"Loading local sample dataset from {sample_file.name}")
        with open(sample_file, "r", encoding="utf-8") as f:
            raw_text = f.read()

        raw_records = self.parse_csv_string(raw_text)
        anomalies, _, _ = process_and_deduplicate_records(raw_records, source_name="NASA FIRMS (Offline Sample Data)")
        return anomalies, "NASA FIRMS (Offline Sample Data)"

    def load_latest_cached_data(self) -> Tuple[List[ThermalAnomaly], str]:
        """Loads the most recently saved processed dataset from backend/data/processed/."""
        latest_file = self.processed_dir / "firms_processed_latest.json"
        if latest_file.exists():
            try:
                logger.info(f"Using cached processed dataset from {latest_file.name}")
                with open(latest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    anomalies = [ThermalAnomaly(**item) for item in data]
                    return anomalies, "NASA FIRMS (Local Cached Data)"
            except Exception as e:
                logger.warning(f"Error reading latest cached JSON: {e}")

        # Search for any processed CSV files
        processed_files = sorted(self.processed_dir.glob("firms_processed_*.csv"), reverse=True)
        if processed_files:
            latest_csv = processed_files[0]
            logger.info(f"Using cached CSV dataset from {latest_csv.name}")
            with open(latest_csv, "r", encoding="utf-8") as f:
                raw_records = self.parse_csv_string(f.read())
            anomalies, _, _ = process_and_deduplicate_records(raw_records, source_name="NASA FIRMS (Cached Data)")
            return anomalies, "NASA FIRMS (Local Cached Data)"

        # If no cache exists, fallback to sample data
        return self.load_local_sample_data()

    def save_datasets(self, raw_csv: str, anomalies: List[ThermalAnomaly]):
        """Persists raw and processed datasets to disk with timestamps."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

        # Save raw response
        raw_filename = f"firms_raw_{timestamp}.csv"
        raw_path = self.raw_dir / raw_filename
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(raw_csv)
        logger.info(f"Raw FIRMS data saved to {raw_path.name}")

        # Save processed CSV
        processed_filename = f"firms_processed_{timestamp}.csv"
        processed_path = self.processed_dir / processed_filename
        if anomalies:
            fieldnames = list(anomalies[0].model_dump().keys())
            with open(processed_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for anomaly in anomalies:
                    writer.writerow(anomaly.model_dump())
            logger.info(f"Processed FIRMS data saved to {processed_path.name}")

            # Save latest JSON cache
            latest_json = self.processed_dir / "firms_processed_latest.json"
            with open(latest_json, "w", encoding="utf-8") as f:
                json.dump([a.model_dump() for a in anomalies], f, indent=2)

    async def get_thermal_anomalies(
        self,
        days: int = settings.FIRMS_DEFAULT_DAYS,
        source: str = settings.FIRMS_DEFAULT_SOURCE,
        country: str = settings.FIRMS_DEFAULT_COUNTRY,
        use_cache: bool = True
    ) -> ThermalAnomalyResponse:
        """
        Primary entry point to retrieve normalized thermal anomaly observations.
        Attempts live API call if configured, falling back gracefully to local cache or sample data.
        """
        raw_csv, error_msg = await self.fetch_live_firms_data(source=source, country=country, days=days)

        if raw_csv:
            raw_records = self.parse_csv_string(raw_csv)
            anomalies, accepted, rejected = process_and_deduplicate_records(
                raw_records,
                source_name=f"NASA FIRMS ({source})"
            )
            self.save_datasets(raw_csv, anomalies)
            data_source = f"NASA FIRMS Live API ({source})"
        else:
            logger.info(f"Live data unavailable ({error_msg}). Falling back to cached/sample data.")
            if use_cache:
                anomalies, data_source = self.load_latest_cached_data()
            else:
                anomalies, data_source = self.load_local_sample_data()

        return ThermalAnomalyResponse(
            status="success",
            count=len(anomalies),
            source=data_source,
            timestamp=datetime.now().isoformat(),
            data=anomalies
        )

# Global service instance
firms_service = FIRMSService()

async def get_thermal_anomalies(days: int = 1, source: str = "VIIRS_SNPP_NRT", country: str = "IND") -> ThermalAnomalyResponse:
    """Convenience wrapper for calling FIRMSService."""
    return await firms_service.get_thermal_anomalies(days=days, source=source, country=country)
