"""
Blood Donor Connection Network (BDCN) - Cloud-Native Enterprise Platform
Core Web Application & Microservices REST Controller
"""
import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify

from services.eligibility_service import fn_validate_donor_eligibility
from services.audit_service import audit_ledger
from services.spatial_service import spatial_cache, haversine_distance_km
from services.reservation_service import reservation_engine
from services.telemetry_service import parse_isbt128_barcode
from services.dispatch_service import dispatch_engine
from services.security_service import security_service

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-bdcn-key-12345")


def safe_float(val, default_val: float) -> float:
    """Safe float conversion guarding against NaN and Inf injections."""
    if val is None:
        return default_val
    s = str(val).strip().lower()
    if s in ("nan", "inf", "-inf", "+inf", "infinity", "-infinity"):
        return default_val
    try:
        return float(s)
    except (ValueError, TypeError):
        return default_val


# Initialize seed data in memory for default demonstrations
reservation_engine.seed_item("W036525000101", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
reservation_engine.seed_item("W036525000102", "PLATELETS", "A", "POSITIVE", "hosp-1")
reservation_engine.seed_item("W036525000103", "RED_BLOOD_CELLS", "B", "POSITIVE", "hosp-1")

spatial_cache.geoadd("marcus_vance", 37.7850, -122.4150, {
    "name": "Marcus Vance",
    "abo_type": "O",
    "rh_factor": "NEGATIVE",
    "rare_antigen_profile": {"kell": "negative", "duffy": "negative"}
})
spatial_cache.geoadd("janesmith", 37.7800, -122.4100, {
    "name": "Jane Smith",
    "abo_type": "O",
    "rh_factor": "NEGATIVE"
})
spatial_cache.geoadd("johndoe", 37.7300, -122.3800, {
    "name": "John Doe",
    "abo_type": "A",
    "rh_factor": "POSITIVE"
})

# In-memory mock databases for legacy view compatibility
demands = [
    {
        "id": 1,
        "hospital": "General Hospital",
        "blood_type": "A+",
        "units": 10,
        "filename": "compliance_doc_A.pdf",
        "status": "Approved",
        "urgency": "Emergency",
        "district": "Downtown"
    },
    {
        "id": 2,
        "hospital": "General Hospital",
        "blood_type": "O-",
        "units": 4,
        "filename": "compliance_doc_B.pdf",
        "status": "Pending",
        "urgency": "Urgent",
        "district": "North District"
    }
]

scheduled_donors = [
    {"name": "John Doe", "blood_type": "A+", "time": "10:30 AM"},
    {"name": "Jane Smith", "blood_type": "O-", "time": "02:15 PM"}
]

alerts = [
    {
        "id": 1,
        "hospital": "General Hospital",
        "blood_type": "A+",
        "status": "Active"
    }
]

audit_logs = [
    {
        "action": "SYSTEM STARTUP",
        "details": "BDCN Core Platform service started successfully.",
        "user": "System",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
]

donors = [
    {
        "name": "Jane Smith",
        "username": "janesmith",
        "age": 28,
        "gender": "Female",
        "blood_group": "O-",
        "last_donation": "2025-11-15",
        "donation_count": 5
    },
    {
        "name": "Marcus Vance",
        "username": "marcus_vance",
        "age": 32,
        "gender": "Male",
        "blood_group": "O-",
        "last_donation": "2024-12-25",
        "donation_count": 8
    },
    {
        "name": "John Doe",
        "username": "johndoe",
        "age": 34,
        "gender": "Male",
        "blood_group": "A+",
        "last_donation": "2025-08-20",
        "donation_count": 2
    }
]

raw_hotspots = [
    {"district": "Downtown", "count": 24, "blood_type": "O-", "distance": 8, "top": 30, "left": 40},
    {"district": "North District", "count": 15, "blood_type": "A+", "distance": 12, "top": 55, "left": 65},
    {"district": "East Valley", "count": 8, "blood_type": "B+", "distance": 22, "top": 70, "left": 30},
    {"district": "South Coast", "count": 19, "blood_type": "O+", "distance": 15, "top": 45, "left": 20},
    {"district": "West Hills", "count": 11, "blood_type": "AB-", "distance": 35, "top": 20, "left": 80}
]


# ==========================================================
# REST API ENDPOINTS (MICROSERVICES TIER)
# ==========================================================

@app.route("/v1/donors/<donor_id>/eligibility", methods=["GET"])
def get_donor_eligibility(donor_id):
    """
    Evaluates rolling donor eligibility per 56-day, 112-day, or 7-day rule.
    """
    donation_type = request.args.get("donation_type", "WHOLE_BLOOD")
    target_date = request.args.get("target_date")

    target_donor = next((d for d in donors if d["username"] == donor_id), None)
    if not target_donor:
        target_donor = {"donor_id": donor_id, "username": donor_id, "is_active": True, "is_deferred": False}

    history = []
    if target_donor.get("last_donation"):
        history.append({
            "donation_type": donation_type,
            "collected_at": target_donor["last_donation"] + "T10:00:00Z"
        })

    result = fn_validate_donor_eligibility(target_donor, history, donation_type=donation_type, target_date=target_date)
    return jsonify(result), 200


@app.route("/v1/inventory/reserve", methods=["POST"])
def reserve_inventory():
    """
    Creates an active 120-minute reservation lease with row-level locking.
    """
    data = request.get_json() or {}
    hospital_id = data.get("hospital_id", "hosp-1")
    clinical_encounter_id = data.get("clinical_encounter_id", "ENC-TRAUMA-9912")
    din_number = data.get("din_number", "W036525000101")
    reserved_by = session.get("username", "Dr. Sarah Lin")

    success, res, err = reservation_engine.create_reservation(
        hospital_id=hospital_id,
        clinical_encounter_id=clinical_encounter_id,
        din_number=din_number,
        reserved_by=reserved_by
    )

    if not success:
        return jsonify({"success": False, "error": err}), 400

    return jsonify({"success": True, "reservation": res}), 201


@app.route("/v1/inventory/consume", methods=["POST"])
def consume_inventory():
    data = request.get_json() or {}
    reservation_id = data.get("reservation_id")
    confirmed_by = session.get("username", "Dr. Sarah Lin")

    success = reservation_engine.confirm_consumption(reservation_id, confirmed_by)
    if not success:
        return jsonify({"success": False, "error": "RESERVATION_NOT_ACTIVE"}), 400

    return jsonify({"success": True, "status": "CONSUMED"}), 200


@app.route("/v1/inventory/reconcile", methods=["POST"])
def reconcile_inventory():
    """
    Executes background auto-release worker for expired leases.
    """
    expired_list = reservation_engine.reconcile_expired_leases()
    return jsonify({"reconciled_count": len(expired_list), "expired": expired_list}), 200


@app.route("/v1/inventory/scan", methods=["POST"])
def scan_inventory():
    data = request.get_json() or {}
    barcode = data.get("barcode", "")
    ok, parsed, err = parse_isbt128_barcode(barcode)
    if not ok:
        return jsonify({"success": False, "error": err}), 400
    return jsonify({"success": True, "parsed": parsed}), 200


@app.route("/v1/spatial/candidates", methods=["GET"])
def find_spatial_candidates():
    """
    Redis 7.x geospatial proximity sweep.
    """
    lat = safe_float(request.args.get("latitude"), 37.7749)
    lon = safe_float(request.args.get("longitude"), -122.4194)
    radius = safe_float(request.args.get("radius_km"), 15.0)
    abo = request.args.get("abo_type")
    rh = request.args.get("rh_factor")
    rare = request.args.get("rare_antigen")

    candidates = spatial_cache.geosearch(
        center_lat=lat,
        center_lon=lon,
        radius_km=radius,
        abo_type=abo,
        rh_factor=rh,
        rare_antigen=rare
    )
    return jsonify({"count": len(candidates), "candidates": candidates}), 200


@app.route("/v1/emergency/dispatch", methods=["POST"])
def create_emergency_dispatch():
    """
    Creates an emergency blood dispatch incident and kicks off state machine.
    """
    data = request.get_json() or {}
    hospital_id = data.get("hospital_id", "hosp-1")
    severity = data.get("severity", "LEVEL_1_CATASTROPHIC")
    required_abo = data.get("required_abo", "O")
    required_rh = data.get("required_rh", "NEGATIVE")
    units = int(data.get("units_requested", 4))
    initiated_by = session.get("username", "ER Clinician")

    disp = dispatch_engine.create_dispatch(
        hospital_id=hospital_id,
        severity=severity,
        required_abo=required_abo,
        required_rh=required_rh,
        units_requested=units,
        initiated_by=initiated_by
    )

    # Enqueue SQS notifications
    dispatch_engine.enqueue_sqs_message({
        "dispatch_id": disp["dispatch_id"],
        "text": f"EMERGENCY: {units} units {required_abo}{required_rh} needed at {hospital_id}"
    })
    dispatch_engine.process_sqs_worker()

    return jsonify(disp), 201


@app.route("/v1/emergency/dispatch/<dispatch_id>", methods=["GET"])
def get_emergency_dispatch(dispatch_id):
    disp = dispatch_engine.get_dispatch(dispatch_id)
    if not disp:
        return jsonify({"error": "NOT_FOUND"}), 404
    return jsonify(disp), 200


@app.route("/v1/emergency/dispatch/<dispatch_id>/status", methods=["PUT"])
def update_emergency_dispatch_status(dispatch_id):
    data = request.get_json() or {}
    next_status = data.get("status")
    updated_by = session.get("username", "System")

    ok, err = dispatch_engine.transition_status(dispatch_id, next_status, updated_by)
    if not ok:
        return jsonify({"success": False, "error": err}), 400
    return jsonify({"success": True, "status": next_status}), 200


@app.route("/v1/audit/verify", methods=["GET"])
def verify_audit_trail():
    is_valid, err = audit_ledger.verify_integrity()
    return jsonify({
        "is_intact": is_valid,
        "error": err,
        "record_count": len(audit_ledger.get_logs())
    }), 200


@app.route("/v1/compliance/worm-export", methods=["POST"])
def export_worm():
    data = request.get_json() or {}
    export_id = data.get("export_id", f"WORM-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}")
    records = audit_ledger.get_logs()
    export = security_service.create_worm_export(export_id, records, session.get("username", "auditor"))
    return jsonify(export), 201


@app.route("/v1/compliance/worm-export/<export_id>/verify", methods=["GET"])
def verify_worm_export(export_id):
    ok, err = security_service.verify_worm_export(export_id)
    return jsonify({"is_valid": ok, "error": err}), 200


# ==========================================================
# UI VIEWS & USER JOURNEYS
# ==========================================================

@app.route("/")
def home():
    if "username" in session:
        if session.get("role") == "hospital":
            return redirect(url_for("hospital_dashboard"))
        elif session.get("role") == "admin":
            return redirect(url_for("admin_queue"))
        elif session.get("role") == "donor":
            return redirect(url_for("donor_profile"))
    return redirect(url_for("login_hospital"))


@app.route("/login/hospital", methods=["GET", "POST"])
def login_hospital():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username and password:
            session["username"] = username
            session["role"] = "hospital"
            audit_logs.append({
                "action": "USER LOGIN",
                "details": f"Hospital user '{username}' logged in successfully.",
                "user": username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash("Logged in to Hospital Portal successfully!", "success")
            return redirect(url_for("hospital_dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("login_hospital.html")


@app.route("/login/donor", methods=["GET", "POST"])
def login_donor():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        target_donor = next((d for d in donors if d["username"] == username), None)
        if target_donor and password:
            session["username"] = username
            session["role"] = "donor"
            audit_logs.append({
                "action": "DONOR LOGIN",
                "details": f"Donor '{username}' logged in successfully.",
                "user": username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash(f"Welcome back, {target_donor['name']}!", "success")
            return redirect(url_for("donor_profile"))
        flash("Invalid credentials.", "danger")
    return render_template("login_donor.html")


@app.route("/login/social/<provider>")
def social_login(provider):
    username = f"social_{provider}_user"
    name = f"Social {provider.capitalize()} User"

    target_donor = next((d for d in donors if d["username"] == username), None)
    if not target_donor:
        target_donor = {
            "name": name,
            "username": username,
            "age": 25,
            "gender": "Other",
            "blood_group": "O+",
            "last_donation": None,
            "donation_count": 1
        }
        donors.append(target_donor)

    session["username"] = username
    session["role"] = "donor"

    audit_logs.append({
        "action": "SOCIAL LOGIN",
        "details": f"User logged in via {provider.capitalize()}.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    flash(f"Successfully authenticated via {provider.capitalize()}!", "success")
    return redirect(url_for("donor_profile"))


@app.route("/donor/register", methods=["GET", "POST"])
def donor_register():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        age = request.form.get("age")
        gender = request.form.get("gender")
        blood_group = request.form.get("blood_group")
        last_donation = request.form.get("last_donation") or None

        if not name or not username or not age or not gender or not blood_group:
            flash("All required fields must be filled.", "danger")
            return redirect(url_for("donor_register"))

        if any(d["username"] == username for d in donors):
            flash("Username already exists.", "danger")
            return redirect(url_for("donor_register"))

        new_donor = {
            "name": name,
            "username": username,
            "age": int(age),
            "gender": gender,
            "blood_group": blood_group,
            "last_donation": last_donation,
            "donation_count": 0
        }
        donors.append(new_donor)

        session["username"] = username
        session["role"] = "donor"
        flash("Registration successful! Welcome to the BDCN family.", "success")
        return redirect(url_for("donor_profile"))

    return render_template("register_donor.html")


@app.route("/donor/profile")
def donor_profile():
    if session.get("role") != "donor":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_donor"))

    username = session.get("username")
    target_donor = next((d for d in donors if d["username"] == username), None)
    if not target_donor:
        flash("Donor profile not found.", "danger")
        return redirect(url_for("logout"))

    count = target_donor.get("donation_count", 0)
    badges = [
        {"name": "Bronze Savior", "description": "Awarded for completing at least 1 voluntary donation.", "earned": count >= 1},
        {"name": "Silver Savior", "description": "Awarded for completing at least 3 voluntary donations.", "earned": count >= 3},
        {"name": "Gold Guardian", "description": "Awarded for completing at least 5 voluntary donations.", "earned": count >= 5}
    ]

    history = []
    if count > 0:
        history.append({
            "location": "Downtown Donation Center",
            "date": target_donor.get("last_donation") or "2025-11-15",
            "units": 1
        })
    if count > 1:
        history.append({
            "location": "North District Clinic",
            "date": "2025-05-10",
            "units": 1
        })

    return render_template("donor_profile.html", donor=target_donor, badges=badges, history=history)


@app.route("/donor/share/<badge_name>", methods=["POST"])
def share_badge(badge_name):
    if session.get("role") != "donor":
        flash("Unauthorized.", "danger")
        return redirect(url_for("login_donor"))

    username = session.get("username")
    clean_badge = badge_name.replace("-", " ")
    flash(f"Successfully shared your {clean_badge} badge to your social profiles!", "success")
    return redirect(url_for("donor_profile"))


@app.route("/login/admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username and password:
            session["username"] = username
            session["role"] = "admin"
            flash("Logged in to Administrator Portal successfully!", "success")
            return redirect(url_for("admin_queue"))
        flash("Invalid credentials.", "danger")
    return render_template("login_admin.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login_hospital"))


@app.route("/hospital/dashboard")
def hospital_dashboard():
    if session.get("role") != "hospital" and session.get("role") != "donor":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_hospital"))

    o_neg_count = reservation_engine.get_available_count("hosp-1", "O", "NEGATIVE")
    return render_template(
        "blood_bank_dashboard.html",
        o_neg_count=o_neg_count,
        platelet_count=4,
        active_leases=2,
        demands=demands,
        scheduled_donors=scheduled_donors
    )


@app.route("/dispatch/command-center")
def dispatch_command_center():
    return render_template("dispatch_command_center.html")


@app.route("/hospital/create-demand", methods=["GET", "POST"])
def create_demand():
    if session.get("role") != "hospital":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_hospital"))

    if request.method == "POST":
        blood_type = request.form.get("blood_type")
        units = request.form.get("units")
        file = request.files.get("document")
        urgency = request.form.get("urgency", "Emergency")
        district = request.form.get("district", "Downtown")

        if not blood_type or not units or not file:
            flash("All fields including compliance document upload are required.", "danger")
            return redirect(url_for("create_demand"))

        new_demand = {
            "id": len(demands) + 1,
            "hospital": session.get("username"),
            "blood_type": blood_type,
            "units": int(units),
            "filename": file.filename,
            "status": "Pending",
            "urgency": urgency,
            "district": district
        }
        demands.append(new_demand)
        flash("Blood demand request submitted successfully for Administrator verification!", "success")
        return redirect(url_for("hospital_dashboard"))

    return render_template("create_demand.html")


@app.route("/admin/queue")
def admin_queue():
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_admin"))

    filter_district = request.args.get("filter_district", "All")
    pending = [d for d in demands if d["status"] == "Pending"]
    if filter_district != "All":
        pending = [d for d in pending if d.get("district") == filter_district]

    return render_template("verification_queue.html", pending_demands=pending, filter_district=filter_district)


@app.route("/admin/verify/<int:demand_id>", methods=["POST"])
def verify_demand(demand_id):
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_admin"))

    action = request.form.get("action")
    target = next((d for d in demands if d["id"] == demand_id), None)
    if target:
        if action == "approve":
            target["status"] = "Approved"
            alerts.append({"id": len(alerts) + 1, "hospital": target["hospital"], "blood_type": target["blood_type"], "status": "Active"})
            flash(f"Approved demand #{demand_id}! Alert dispatched to nearby donors.", "success")
        elif action == "reject":
            target["status"] = "Rejected"
            flash(f"Rejected demand #{demand_id}.", "warning")
    return redirect(url_for("admin_queue"))


@app.route("/admin/alerts")
def admin_alerts():
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_admin"))
    return render_template("alert_management.html", alerts=alerts)


@app.route("/admin/audit-log")
def admin_audit_log():
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_admin"))
    return render_template("audit_log.html", logs=audit_logs)


@app.route("/map/hotspots")
def map_hotspots():
    radius = int(request.args.get("radius", 50))
    blood_type = request.args.get("blood_type", "All")
    filtered = [h for h in raw_hotspots if h["distance"] <= radius]
    if blood_type != "All":
        filtered = [h for h in filtered if h["blood_type"] == blood_type]
    return render_template("map_hotspots.html", hotspots=filtered, radius=radius, blood_type=blood_type)


if __name__ == "__main__":
    is_debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    bind_host = os.environ.get("FLASK_HOST", "127.0.0.1")
    app.run(host=bind_host, port=5000, debug=is_debug)
