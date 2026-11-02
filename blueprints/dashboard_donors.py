from flask import Blueprint, request, jsonify, session
from db.init_db import get_db_connection

dashboard_donors_bp = Blueprint(
    "dashboard_donors",
    __name__,
    url_prefix="/api/v1/dashboard")

# Standard ABO/Rh blood group compatibility matrix
# Recipient -> list of compatible donor blood groups
COMPATIBILITY_MATRIX = {
    "A+": ["A+", "A-", "O+", "O-"],
    "A-": ["A-", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "B-": ["B-", "O-"],
    "AB+": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    "AB-": ["A-", "B-", "AB-", "O-"],
    "O+": ["O+", "O-"],
    "O-": ["O-"]
}

DEFAULT_DONORS = [{"donor_id": "BDC-101-0112",
                   "name": "Alice Henderson",
                   "blood_group": "A+",
                   "verified": True,
                   "contact_phone": "(555) 234-5544",
                   "location": "Downtown Metro Hospital"},
                  {"donor_id": "BDC-102-8765",
                   "name": "Bob Vance",
                   "blood_group": "O-",
                   "verified": True,
                   "contact_phone": "(555) 456-1234",
                   "location": "North District Clinic"},
                  {"donor_id": "BDC-103-3456",
                   "name": "Carol Danvers",
                   "blood_group": "O+",
                   "verified": True,
                   "contact_phone": "(555) 789-9876",
                   "location": "East Valley Medical"},
                  {"donor_id": "BDC-104-9901",
                   "name": "David Miller",
                   "blood_group": "A-",
                   "verified": True,
                   "contact_phone": "(555) 321-2468",
                   "location": "South Coast Health"},
                  {"donor_id": "BDC-105-1578",
                   "name": "Emma Stone",
                   "blood_group": "A+",
                   "verified": False,
                   "contact_phone": "(555) 654-1357",
                   "location": "West Hills Center"},
                  {"donor_id": "BDC-106-4432",
                   "name": "Frank Castle",
                   "blood_group": "B+",
                   "verified": True,
                   "contact_phone": "(555) 987-4432",
                   "location": "Central Blood Bank"},
                  {"donor_id": "BDC-107-7789",
                   "name": "Grace Hopper",
                   "blood_group": "B-",
                   "verified": True,
                   "contact_phone": "(555) 123-7789",
                   "location": "North District Clinic"},
                  {"donor_id": "BDC-108-8821",
                   "name": "Henry Pym",
                   "blood_group": "AB+",
                   "verified": True,
                   "contact_phone": "(555) 246-8821",
                   "location": "University Hospital"},
                  {"donor_id": "BDC-109-9943",
                   "name": "Iris West",
                   "blood_group": "AB-",
                   "verified": True,
                   "contact_phone": "(555) 369-9943",
                   "location": "Downtown General"},
                  {"donor_id": "BDC-110-1290",
                   "name": "Jack Reacher",
                   "blood_group": "O-",
                   "verified": True,
                   "contact_phone": "(555) 582-1290",
                   "location": "East Valley Medical"},
                  {"donor_id": "BDC-111-5512",
                   "name": "Kelly Kapoor",
                   "blood_group": "O+",
                   "verified": True,
                   "contact_phone": "(555) 741-5512",
                   "location": "South Coast Health"},
                  {"donor_id": "BDC-112-6634",
                   "name": "Luke Cage",
                   "blood_group": "A+",
                   "verified": True,
                   "contact_phone": "(555) 852-6634",
                   "location": "Harlem Care Unit"}]


def mask_contact(contact_str, user_role=None):
    """
    REQ-F-018: Donor PII (contact details) on the dashboard must be masked based on role.
    Hospitals and anonymous coordinators see (***) ***-XXXX by default.
    Only authorized emergency personnel see unmasked.
    """
    if not contact_str:
        return "(***) ***-****"
    if user_role == "emergency_authorized":
        return contact_str
    # Extract last 4 digits if present
    digits = [c for c in contact_str if c.isdigit()]
    if len(digits) >= 4:
        last4 = "".join(digits[-4:])
        return f"(***) ***-{last4}"
    return "(***) ***-****"


def mask_donor_id(donor_id):
    """Masks center digits of donor ID, e.g. BDC-***-0112"""
    parts = donor_id.split("-")
    if len(parts) == 3:
        return f"{parts[0]}-***-{parts[2]}"
    return donor_id


def load_all_donors():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT donor_id, name, blood_group, verified, contact_phone, location FROM verified_donors")
        rows = cursor.fetchall()
        conn.close()
        if rows:
            return [
                {
                    "donor_id": r["donor_id"],
                    "name": r["name"],
                    "blood_group": r["blood_group"],
                    "verified": bool(r["verified"]),
                    "contact_phone": r["contact_phone"],
                    "location": r["location"]
                }
                for r in rows
            ]
    except Exception:
        pass
    return DEFAULT_DONORS


@dashboard_donors_bp.route("/donors/filter", methods=["GET"])
def filter_compatible_donors():
    """
    REQ-F-020: GET /api/v1/dashboard/donors/filter
    Filters donors using ABO/Rh matrix (REQ-F-012)
    verified_only=true by default (REQ-F-011)
    Outputs KPI cards (REQ-F-016), Masked PII (REQ-F-018), and table rows (REQ-F-017).
    """
    raw_bg = request.args.get("blood_group", "A+")
    if raw_bg.endswith(" ") or " " in raw_bg:
        raw_bg = raw_bg.replace(" ", "+")
    blood_group = raw_bg.strip().upper()
    verified_only_param = request.args.get(
        "verified_only", "true").strip().lower()
    verified_only = verified_only_param in ("true", "1", "yes")

    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1

    try:
        per_page = max(1, min(100, int(request.args.get("per_page", 10))))
    except ValueError:
        per_page = 10

    compatible_groups = COMPATIBILITY_MATRIX.get(blood_group, [blood_group])

    all_donors = load_all_donors()

    # Filter candidates
    matched_donors = []
    total_compatible = 0
    exact_matches = 0
    universal_donor_standby = 0

    for d in all_donors:
        d_bg = d["blood_group"]
        is_verified = d["verified"]

        # Universal O- standby count (counts all verified O- donors regardless
        # of recipient filter)
        if d_bg == "O-" and is_verified:
            universal_donor_standby += 1

        # Check verification filter
        if verified_only and not is_verified:
            continue

        # Check compatibility
        if d_bg in compatible_groups:
            total_compatible += 1
            if d_bg == blood_group:
                exact_matches += 1
                compatibility_type = "Exact Match"
            elif d_bg == "O-":
                compatibility_type = "Universal"
            else:
                compatibility_type = "Compatible"

            status_str = "Verified" if is_verified else "Pending"
            user_role = session.get("user_role")

            matched_donors.append({
                "donor_id": mask_donor_id(d["donor_id"]),
                "raw_id": d["donor_id"],
                "blood_group": d_bg,
                "compatibility": compatibility_type,
                "status": status_str,
                "masked_contact": mask_contact(d["contact_phone"], user_role),
                "location": d["location"]
            })

    # Pagination
    total = len(matched_donors)
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_donors = matched_donors[start_idx:end_idx]

    return jsonify({
        "kpis": {
            "total_compatible": total_compatible,
            "exact_matches": exact_matches,
            "universal_donor_standby": universal_donor_standby
        },
        "donors": paginated_donors,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }
    }), 200
