"""
Telemetry Service - ISBT 128 Barcode Scanning & Cold-Chain Telemetry Ingestion
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple


def parse_isbt128_barcode(barcode_str: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Parses and validates ISBT 128 Donation Identification Number (DIN).
    Standard DIN format: =GNNNNYYNNNNNNKK (e.g., =W03652500010100) or plain DIN W036525000101.
    """
    cleaned = barcode_str.strip().lstrip("=")
    if not cleaned or len(cleaned) < 13:
        return False, None, "INVALID_ISBT128_LENGTH"

    # Match country code (1 letter) + facility code (4 alphanumeric) + year (2 digits) + sequence (6 digits)
    din_match = re.match(r"^([A-Z]\d{4})(\d{2})(\d{6})", cleaned)
    if not din_match:
        # Fallback accept alphanumeric DIN
        if re.match(r"^[A-Z0-9]{13,16}$", cleaned):
            return True, {
                "din_number": cleaned[:13],
                "facility_code": cleaned[:5],
                "year": "20" + cleaned[5:7],
                "sequence": cleaned[7:13],
                "raw_barcode": barcode_str
            }, None
        return False, None, "INVALID_ISBT128_FORMAT"

    facility, year, seq = din_match.groups()
    din_number = f"{facility}{year}{seq}"

    return True, {
        "din_number": din_number,
        "facility_code": facility,
        "year": "20" + year,
        "sequence": seq,
        "raw_barcode": barcode_str
    }, None
