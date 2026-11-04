"""
Matching service module for Blood Donor Connection Network (BDCN).
Provides clinical ABO/Rh blood compatibility matching for urgent blood group requests.
"""
from typing import List, Dict, Any, Set
from functools import lru_cache

# Standard Red Blood Cell (RBC) compatibility table:
# Key = Recipient's Blood Group (what is urgently requested)
# Value = Tuple of Compatible Donor Blood Groups that can safely donate to this recipient
BLOOD_COMPATIBILITY_MATRIX: Dict[str, tuple] = {
    "O-": ("O-",),
    "O+": ("O-", "O+"),
    "A-": ("O-", "A-"),
    "A+": ("O-", "O+", "A-", "A+"),
    "B-": ("O-", "B-"),
    "B+": ("O-", "O+", "B-", "B+"),
    "AB-": ("O-", "A-", "B-", "AB-"),
    "AB+": ("O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"),
}


@lru_cache(maxsize=32)
def get_compatible_donor_types(recipient_blood_group: str) -> tuple:
    """
    Get compatible donor blood groups for a given recipient blood group with LRU cache.
    Normalizes casing and whitespace.
    """
    cleaned = recipient_blood_group.strip().upper()
    return BLOOD_COMPATIBILITY_MATRIX.get(cleaned, ())


def is_compatible(donor_blood_group: str, recipient_blood_group: str) -> bool:
    """Check if donor blood group is compatible with recipient blood group."""
    compatible_types = get_compatible_donor_types(recipient_blood_group)
    return donor_blood_group.strip().upper() in compatible_types


def mask_contact_info(phone: str) -> str:
    """Mask contact phone number for donor privacy compliance."""
    if not phone:
        return "+1-XXX-XXX-0000"
    cleaned = phone.strip()
    if len(cleaned) > 4:
        return f"+1-XXX-XXX-{cleaned[-4:]}"
    return "+1-XXX-XXX-" + cleaned


def filter_compatible_donors(
    donors_list: List[Dict[str, Any]],
    requested_blood_group: str
) -> List[Dict[str, Any]]:
    """
    Filters a donor list to return only compatible donors for the requested blood group.
    Standardizes output format with donor_id, blood_type, and contact_information.
    """
    compatible_types: Set[str] = set(get_compatible_donor_types(requested_blood_group))
    results: List[Dict[str, Any]] = []

    for idx, donor in enumerate(donors_list):
        # Blood type could be stored in 'blood_group' or 'blood_type'
        b_type = (donor.get("blood_group") or donor.get("blood_type") or "").strip().upper()
        if b_type in compatible_types:
            donor_id = donor.get("donor_id") or f"DN-{str(idx + 1).zfill(5)}"
            raw_contact = donor.get("contact") or donor.get("phone") or donor.get("username", "1234")
            contact_info = donor.get("contact_information") or mask_contact_info(str(raw_contact))
            
            results.append({
                "donor_id": donor_id,
                "name": donor.get("name", "Anonymous Donor"),
                "blood_type": b_type,
                "contact_information": contact_info,
                "is_verified": donor.get("is_verified", True),
                "district": donor.get("district", "Downtown")
            })

    return results
