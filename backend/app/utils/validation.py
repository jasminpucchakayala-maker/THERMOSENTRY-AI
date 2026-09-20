import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
from backend.app.models.thermal_anomaly import ThermalAnomaly
from backend.app.utils.logging_config import logger

def parse_float(val: Any) -> Optional[float]:
    """Safely parse float values, returning None if parsing fails."""
    if val is None or val == "" or str(val).strip().lower() in ["nan", "null", "none"]:
        return None
    try:
        f = float(val)
        return f if not (f != f) else None # check for NaN
    except (ValueError, TypeError):
        return None

def parse_confidence(val: Any) -> Optional[float]:
    """
    Parses FIRMS confidence values.
    FIRMS VIIRS confidence can be categorical ('l'=low, 'n'=nominal, 'h'=high)
    or MODIS confidence (0-100 numeric).
    """
    if val is None or val == "":
        return None
    val_str = str(val).strip().lower()
    mapping = {"l": 30.0, "low": 30.0, "n": 60.0, "nominal": 60.0, "h": 90.0, "high": 90.0}
    if val_str in mapping:
        return mapping[val_str]
    parsed = parse_float(val_str)
    if parsed is not None:
        return max(0.0, min(100.0, parsed))
    return None

def validate_date(date_str: str) -> Optional[str]:
    """Validates date string and formats to YYYY-MM-DD."""
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y%m%d"]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None

def validate_time(time_str: str) -> str:
    """Standardizes time string to 4-digit HHMM format."""
    if time_str is None:
        return "0000"
    t = str(time_str).strip().zfill(4)
    if re.match(r"^\d{4}$", t):
        return t
    return "0000"

def clean_and_normalize_record(row: Dict[str, Any], source_name: str = "NASA FIRMS") -> Tuple[Optional[ThermalAnomaly], Optional[str]]:
    """
    Validates a raw record dictionary and transforms it into a ThermalAnomaly object.
    Returns (ThermalAnomaly, None) if valid, or (None, rejection_reason) if invalid.
    """
    # Normalize dictionary keys to lowercase and strip whitespace
    clean_row = {str(k).strip().lower(): v for k, v in row.items()}

    # Extract required coordinates
    lat_val = parse_float(clean_row.get("latitude") or clean_row.get("lat"))
    lon_val = parse_float(clean_row.get("longitude") or clean_row.get("lon") or clean_row.get("long"))

    if lat_val is None or not (-90.0 <= lat_val <= 90.0):
        return None, f"Invalid latitude: {clean_row.get('latitude')}"
    if lon_val is None or not (-180.0 <= lon_val <= 180.0):
        return None, f"Invalid longitude: {clean_row.get('longitude')}"

    # Extract date & time
    raw_date = clean_row.get("acq_date") or clean_row.get("acquisition_date") or clean_row.get("date")
    norm_date = validate_date(str(raw_date) if raw_date else "")
    if not norm_date:
        return None, f"Invalid acquisition date: {raw_date}"

    raw_time = clean_row.get("acq_time") or clean_row.get("acquisition_time") or clean_row.get("time")
    norm_time = validate_time(raw_time)

    # Satellite & Instrument
    satellite = str(clean_row.get("satellite") or clean_row.get("sat") or "UNKNOWN").strip().upper()
    instrument = str(clean_row.get("instrument") or clean_row.get("inst") or "VIIRS").strip().upper()

    # Optional measurements
    confidence = parse_confidence(clean_row.get("confidence") or clean_row.get("conf"))
    
    # Brightness temperature (check bright_ti4, bright_t21, brightness, or temperature)
    bright_temp = parse_float(
        clean_row.get("bright_ti4") or 
        clean_row.get("bright_t21") or 
        clean_row.get("brightness") or 
        clean_row.get("brightness_temperature")
    )
    
    frp = parse_float(clean_row.get("frp"))

    day_night_raw = str(clean_row.get("daynight") or clean_row.get("day_night") or "").strip().upper()
    day_night = day_night_raw if day_night_raw in ["D", "N"] else None

    # Generate unique composite ID
    record_id = ThermalAnomaly.generate_id(lat_val, lon_val, norm_date, norm_time, satellite)

    anomaly = ThermalAnomaly(
        id=record_id,
        latitude=round(lat_val, 4),
        longitude=round(lon_val, 4),
        acquisition_date=norm_date,
        acquisition_time=norm_time,
        satellite=satellite,
        instrument=instrument,
        confidence=confidence,
        brightness_temperature=round(bright_temp, 1) if bright_temp is not None else None,
        frp=round(frp, 1) if frp is not None else None,
        day_night=day_night,
        source=source_name
    )

    return anomaly, None

def process_and_deduplicate_records(
    raw_records: List[Dict[str, Any]], 
    source_name: str = "NASA FIRMS"
) -> Tuple[List[ThermalAnomaly], int, int]:
    """
    Processes a list of raw record dictionaries, applying validation and deduplication.
    Returns (valid_anomalies, accepted_count, rejected_count).
    """
    valid_anomalies: List[ThermalAnomaly] = []
    seen_ids = set()
    accepted = 0
    rejected = 0

    for idx, raw in enumerate(raw_records):
        anomaly, error_msg = clean_and_normalize_record(raw, source_name=source_name)
        if anomaly is None:
            rejected += 1
            logger.debug(f"Record index {idx} rejected: {error_msg}")
            continue

        if anomaly.id in seen_ids:
            rejected += 1
            logger.debug(f"Record index {idx} rejected: Duplicate ID {anomaly.id}")
            continue

        seen_ids.add(anomaly.id)
        valid_anomalies.append(anomaly)
        accepted += 1

    logger.info(f"Record cleaning summary — Received: {len(raw_records)}, Accepted: {accepted}, Rejected/Duplicates: {rejected}")
    return valid_anomalies, accepted, rejected
