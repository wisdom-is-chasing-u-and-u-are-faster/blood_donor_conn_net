import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from db.init_db import get_db_connection

prescreening_bp = Blueprint(
    "prescreening",
    __name__,
    url_prefix="/api/v1/prescreening")

# In-memory storage fallback for tests or when DB is initialized
prescreening_records = []


def evaluate_rules(
        age,
        weight,
        last_donation_days,
        chronic_conditions=False,
        recent_travel=False):
    """
    REQ-F-002: Clinical evaluation rules:
    - age >= 18
    - weight >= 50.0 kg
    - recent donation interval >= 56 days
    - no chronic conditions
    - no recent high-risk travel
    """
    reasons = []
    if age is None or age < 18:
        reasons.append("you must be at least 18 years old")
    if weight is None or weight < 50.0:
        reasons.append("your weight must be at least 50kg")
    if last_donation_days is None or last_donation_days < 56:
        reasons.append("you must wait at least 56 days between donations")
    if chronic_conditions:
        reasons.append("of your answer regarding chronic conditions")
    if recent_travel:
        reasons.append("of your answer regarding recent travel")

    status = "Deferred" if reasons else "Eligible"
    return status, reasons


@prescreening_bp.route("/evaluate", methods=["POST"])
def evaluate_prescreening():
    """
    REQ-F-005: POST /api/v1/prescreening/evaluate
    Evaluates donor eligibility and persists into donor_prescreenings database table (REQ-F-007).
    """
    data = request.get_json() or request.form.to_dict()

    try:
        age = int(data.get("age", 0))
    except (ValueError, TypeError):
        age = None

    try:
        weight = float(data.get("weight", 0.0))
    except (ValueError, TypeError):
        weight = None

    try:
        last_donation_days = int(
            data.get("last_donation_days") or data.get("last_donation") or 0)
    except (ValueError, TypeError):
        last_donation_days = None

    chronic_conditions = str(
        data.get(
            "chronic_conditions",
            "")).lower() in (
        "true",
        "1",
        "on",
        "yes")
    recent_travel = str(
        data.get(
            "recent_travel",
            "")).lower() in (
        "true",
        "1",
        "on",
        "yes")
    donor_id = data.get("donor_id", "ANON-" +
                        datetime.now().strftime("%Y%m%d%H%M%S"))

    status, reasons = evaluate_rules(
        age, weight, last_donation_days, chronic_conditions, recent_travel)

    prescreening_id = len(prescreening_records) + 1
    timestamp = datetime.now(timezone.utc).isoformat()

    # Persist in SQLite DB (REQ-F-007) with fallback
    try:
        conn = get_db_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO donor_prescreenings
                (donor_id, age, weight, last_donation_days, chronic_conditions, recent_travel, status, reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (donor_id, age or 0, weight or 0.0, last_donation_days or 0,
                  1 if chronic_conditions else 0, 1 if recent_travel else 0,
                  status, json.dumps(reasons)))
            prescreening_id = cursor.lastrowid
        conn.close()
    except Exception:
        # Fallback to in-memory list if DB file lock / path issue occurs
        pass

    record = {
        "id": prescreening_id,
        "donor_id": donor_id,
        "age": age,
        "weight": weight,
        "last_donation_days": last_donation_days,
        "chronic_conditions": chronic_conditions,
        "recent_travel": recent_travel,
        "status": status,
        "reasons": reasons,
        "created_at": timestamp
    }
    prescreening_records.append(record)

    return jsonify({
        "status": status,
        "reasons": reasons,
        "prescreening_id": prescreening_id,
        "timestamp": timestamp
    }), 200
