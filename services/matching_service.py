"""
Matching Service for Urgent Blood Group Requests.
Provides:
- In-memory clinical ABO/Rh compatibility matrix with LRU cache (CONSTRAINT-002, REQ-F-007)
- Filtering for verified donors only (REQ-F-008)
- Ultra-fast matching latency (<3s and sub-200ms p95, REQ-N-002, REQ-N-003)
"""
from functools import lru_cache
from typing import List, Dict, Any, Set, Tuple

# Red Blood Cell Compatibility Matrix (Recipients receive from Donors):
# Recipient: Compatible Donors
# O-  can receive from: O-
# O+  can receive from: O-, O+
# B-  can receive from: O-, B-
# B+  can receive from: O-, O+, B-, B+
# A-  can receive from: O-, A-
# A+  can receive from: O-, O+, A-, A+
# AB- can receive from: O-, B-, A-, AB-
# AB+ can receive from: O-, O+, B-, B+, A-, A+, AB-, AB+ (Universal recipient)

COMPATIBILITY_MATRIX: Dict[str, Tuple[str, ...]] = {
    "O-": ("O-",),
    "O+": ("O-", "O+"),
    "A-": ("O-", "A-"),
    "A+": ("O-", "O+", "A-", "A+"),
    "B-": ("O-", "B-"),
    "B+": ("O-", "O+", "B-", "B+"),
    "AB-": ("O-", "A-", "B-", "AB-"),
    "AB+": ("O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+")
}


@lru_cache(maxsize=128)
def get_compatible_donor_blood_types(recipient_blood_type: str) -> Tuple[str, ...]:
    """
    Returns tuple of compatible donor blood groups for a given recipient blood type.
    Uses LRU cache for high-throughput sub-millisecond retrieval.
    """
    cleaned = recipient_blood_type.strip().upper() if recipient_blood_type else ""
    return COMPATIBILITY_MATRIX.get(cleaned, ())


def filter_compatible_verified_donors(
    donors_list: List[Dict[str, Any]],
    requested_blood_type: str
) -> Dict[str, Any]:
    """
    Filters donors by clinical ABO/Rh compatibility and verification status.
    Guarantees:
    - Only 'verified' donors are matched (REQ-F-008, AC 3)
    - Blood compatibility matching via matrix (REQ-F-007, AC 1)
    """
    cleaned_type = (requested_blood_type or "").strip().upper()
    
    if cleaned_type == "ALL" or not cleaned_type:
        compatible_types = tuple(COMPATIBILITY_MATRIX.keys())
    else:
        compatible_types = get_compatible_donor_blood_types(cleaned_type)

    matched = []
    for donor in donors_list:
        # Check verification status
        is_verified = (
            donor.get("is_verified") is True or
            str(donor.get("verification_status", "")).lower() == "verified" or
            str(donor.get("is_verified", "")).lower() in ["true", "1", "verified"]
        )
        if not is_verified:
            continue

        donor_blood = (donor.get("blood_group") or donor.get("blood_type") or "").strip().upper()
        if donor_blood in compatible_types:
            matched.append(donor)

    return {
        "requested_blood_type": cleaned_type,
        "compatible_types": list(compatible_types),
        "matched_donors": matched,
        "total_matches": len(matched)
    }
