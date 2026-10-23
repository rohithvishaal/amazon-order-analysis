"""Data cleaning, normalization, and parsing utilities for Amazon order records."""

from datetime import datetime
import re
from typing import Any, Optional, Tuple
from zoneinfo import ZoneInfo

from .config import CARRIER_MAPPING, INDIAN_STATES, POPULAR_CITIES, TAXONOMY_RULES

IST_ZONE = ZoneInfo("Asia/Kolkata")

# Prepare precompiled regex patterns for universal address parsing
_SORTED_STATES = sorted(INDIAN_STATES, key=len, reverse=True)
_STATES_PATTERN = "|".join(re.escape(s) for s in _SORTED_STATES)
_IN_ADDR_REGEX = re.compile(
    rf"([A-Za-z0-9\s,/\.\-]+?)\s+({_STATES_PATTERN})\s+(\d{{6}})(?:\s+India)?",
    re.IGNORECASE,
)
_US_ADDR_REGEX = re.compile(
    r"([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)",
    re.IGNORECASE,
)


def clean_amount(val: Any) -> float:
    """Parse monetary amounts robustly.
    
    Handles formats like '2,499', \"'-1,800'\", '₹370.48', negative strings,
    and missing values safely.
    """
    if val is None or pd_isna(val):
        return 0.0
    
    val_str = str(val).strip().strip("'\"")
    if not val_str or val_str.lower() in ("not available", "not applicable", "none", "-", ""):
        return 0.0
    
    # Strip currency symbols and whitespace
    cleaned = re.sub(r"[₹$€£\s,]", "", val_str)
    
    # Handle negative numbers wrapped in parentheses or single quotes like '(100)'
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
        
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_datetime_ist(val: Any) -> Optional[datetime]:
    """Parse ISO 8601 or date strings into timezone-aware IST datetimes."""
    if not val or pd_isna(val):
        return None
    
    val_str = str(val).strip()
    if val_str.lower() in ("not available", "not applicable", "none", ""):
        return None
    
    # Normalize trailing Z to standard offset
    if val_str.endswith("Z"):
        val_str = val_str[:-1] + "+00:00"
    
    try:
        dt = datetime.fromisoformat(val_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt.astimezone(IST_ZONE)
    except Exception:
        # Fallback regex parsing for format YYYY-MM-DD
        match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", val_str)
        if match:
            y, m, d = map(int, match.groups())
            return datetime(y, m, d, tzinfo=IST_ZONE)
        return None


def pd_isna(val: Any) -> bool:
    """Check if value is NaN or None without requiring external dependencies."""
    if val is None:
        return True
    try:
        return val != val
    except Exception:
        return False


def extract_city(address: Any) -> str:
    """Extract standard city name from any shipping address string universally.
    
    Uses high-speed catalog matching combined with dynamic regex heuristics
    for Indian, US, and international addresses.
    """
    if not address or pd_isna(address):
        return "Not Available"
    addr_str = str(address).strip()
    if addr_str.lower() in ("not available", "not applicable", "none", ""):
        return "Not Available"
    
    # Check popular cities catalog (prefer match closest to the end of the address)
    best_city = None
    best_pos = -1
    for c_key, c_name in POPULAR_CITIES.items():
        for m in re.finditer(rf"\b{re.escape(c_key)}\b", addr_str, re.IGNORECASE):
            if m.start() > best_pos:
                best_pos = m.start()
                best_city = c_name
    
    if best_city:
        return best_city
    
    # Fallback 1: Dynamic Indian address format (... <CITY> <STATE> <PINCODE> India)
    m_in = _IN_ADDR_REGEX.search(addr_str)
    if m_in:
        pre_state = m_in.group(1).strip()
        tokens = re.split(r"[,/]+", pre_state)
        candidate = tokens[-1].strip()
        words = candidate.split()
        if len(words) >= 2 and words[-2].upper() in ("NEW", "SOUTH", "NORTH", "WEST", "EAST", "GREATER", "NAVI"):
            return f"{words[-2]} {words[-1]}".title()
        elif words:
            return words[-1].title()
            
    # Fallback 2: Dynamic US address format (... <CITY>, <STATE> <ZIP>)
    m_us = _US_ADDR_REGEX.search(addr_str)
    if m_us:
        city_raw = m_us.group(1).strip()
        tokens = re.split(r"[,/]+", city_raw)
        return tokens[-1].strip().title()
        
    return "Other Location"


def parse_carrier(carrier_field: Any) -> Tuple[str, str]:
    """Parse Carrier Name and Tracking Number from combined field.
    
    Returns (Carrier Name, Tracking Number).
    """
    if not carrier_field or pd_isna(carrier_field):
        return ("Not Available", "")
    
    field_str = str(carrier_field).strip()
    if field_str.lower() in ("not available", "not applicable", "none", ""):
        return ("Not Available", "")
    
    # Patterns like 'ATS(260752802370)' or 'Delhivery(12345)' or 'SVAFN'
    match = re.match(r"^([A-Za-z0-9_\s-]+)\s*\(([^)]+)\)$", field_str)
    if match:
        code, tracking = match.groups()
        code_upper = code.strip().upper()
        carrier_name = CARRIER_MAPPING.get(code_upper, code.strip())
        return (carrier_name, tracking.strip())
    
    # No parentheses - match code
    code_match = re.match(r"^([A-Za-z0-9_\s]+)", field_str)
    if code_match:
        code_upper = code_match.group(1).strip().upper()
        carrier_name = CARRIER_MAPPING.get(code_upper, field_str)
        return (carrier_name, "")
    
    return (field_str, "")


def classify_product(title: str) -> Tuple[str, str]:
    """Classify product into (Macro Category, Subcategory) using active taxonomy rules."""
    if not title or pd_isna(title):
        return ("General Merchandise", "Unspecified")
    
    title_lower = str(title).lower()
    for macro_cat, sub_cat, patterns in TAXONOMY_RULES:
        for pat in patterns:
            if re.search(pat, title_lower):
                return (macro_cat, sub_cat)
    
    return ("General Merchandise", "Miscellaneous")


def standardize_status(order_status: str, shipment_status: str = "", returns_info: Optional[dict] = None) -> str:
    """Compute normalized lifecycle status for an order."""
    if returns_info:
        if returns_info.get("resolution") == "Exchange" or returns_info.get("is_replacement"):
            return "Replaced / Exchanged"
        return "Returned & Refunded"
    
    o_stat = (order_status or "").strip().lower()
    s_stat = (shipment_status or "").strip().lower()
    
    if "cancel" in o_stat or "cancel" in s_stat:
        return "Cancelled"
    if "return" in o_stat or "refund" in o_stat:
        return "Returned"
    if "closed" in o_stat or "delivered" in o_stat or "shipped" in s_stat:
        return "Delivered"
    if "authoriz" in o_stat or "in transit" in s_stat or "arriving" in o_stat:
        return "In Transit / Arriving"
    
    return "Delivered"
