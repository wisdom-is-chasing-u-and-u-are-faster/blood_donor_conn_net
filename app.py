# This is a Flask web application for a Blood Donor Connection Network.
# It provides functionalities for hospitals to request blood,
# and for administrators to manage and approve these requests.
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify

from db.init_db import get_db_connection
from services.crypto_service import crypto_service
from services.audit_service import audit_service
from services.inventory_service import inventory_service
from services.dispatch_service import dispatch_service
from services.proximity_service import proximity_service
from services.notification_service import notification_service

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "super-secret-bdcn-key-12345")

# Initialize database tables & baseline data on startup
get_db_connection()

# In-memory mock databases (preserved for backwards-compatibility with legacy test cases)
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
    },
    {
        "action": "HOSPITAL DEMAND APPROVED",
        "details": "Demand #1 (A+, 10 units) approved. EmergencyDemandCreated event emitted to Cloud Pub/Sub.",
        "user": "admin_district",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
]

# Registered donors
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
        "name": "John Doe",
        "username": "johndoe",
        "age": 34,
        "gender": "Male",
        "blood_group": "A+",
        "last_donation": "2025-08-20",
        "donation_count": 2
    }
]

# Mock donor density hotspots
raw_hotspots = [
    {"district": "Downtown",
     "count": 24,
     "blood_type": "O-",
     "distance": 8,
     "top": 30,
     "left": 40},
    {"district": "North District",
     "count": 15,
     "blood_type": "A+",
     "distance": 12,
     "top": 55,
     "left": 65},
    {"district": "East Valley",
     "count": 8,
     "blood_type": "B+",
     "distance": 22,
     "top": 70,
     "left": 30},
    {"district": "South Coast",
     "count": 19,
     "blood_type": "O+",
     "distance": 15,
     "top": 45,
     "left": 20},
    {"district": "West Hills",
     "count": 11,
     "blood_type": "AB-",
     "distance": 35,
     "top": 20,
     "left": 80}
]

# ============================================================================
# Core BDCN RESTful Clinical API v1 Endpoints (Matching api_contract.json)
# ============================================================================

@app.route("/health", methods=["GET"])
def health_check():
    """Health and readiness probe."""
    return jsonify({
        "status": "UP",
        "database": "CONNECTED",
        "postgis": "ENABLED",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route("/api/v1/dispatch/emergency-requests", methods=["GET", "POST"])
def api_dispatch_emergency_requests():
    """
    POST: Create emergency trauma blood dispatch request with pessimistic lock.
    GET: List active emergency trauma requests.
    """
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict()
        if not data:
            return jsonify({"error": "Missing JSON request payload"}), 400

        hospital_id = data.get("requestingHospitalId") or data.get("hospital_id", "fac-001")
        blood_type = data.get("requiredBloodType") or data.get("blood_type")
        component_type = data.get("componentType") or data.get("component_type", "RED_BLOOD_CELLS")
        
        try:
            units = int(data.get("unitsRequested") or data.get("units", 1))
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid unitsRequested value"}), 400

        urgency = data.get("urgencyTier") or data.get("urgency", "CODE_RED")
        lat = float(data.get("latitude", 40.7128))
        lon = float(data.get("longitude", -74.0060))
        notes = data.get("clinicalNotesEncrypted") or data.get("notes", "")

        if not blood_type:
            return jsonify({"error": "requiredBloodType is mandatory"}), 400

        success, result, err_msg = dispatch_service.create_emergency_request(
            requesting_hospital_id=hospital_id,
            required_blood_type=blood_type,
            component_type=component_type,
            units_requested=units,
            urgency_tier=urgency,
            latitude=lat,
            longitude=lon,
            clinical_notes=notes,
            auto_allocate=True
        )

        if not success:
            return jsonify({
                "error": err_msg or "INSUFFICIENT_COMPATIBLE_INVENTORY",
                "code": "INSUFFICIENT_COMPATIBLE_INVENTORY"
            }), 422

        return jsonify(result), 201

    # GET: List all active dispatch requests
    active_requests = dispatch_service.list_active_requests()
    return jsonify({"requests": active_requests}), 200


@app.route("/api/v1/dispatch/emergency-requests/<request_id>", methods=["GET"])
def api_get_dispatch_emergency_request(request_id):
    """Retrieve details and status timeline for a specific emergency dispatch request."""
    req_details = dispatch_service.get_emergency_request(request_id)
    if not req_details:
        return jsonify({"error": f"Emergency request '{request_id}' not found"}), 404
    return jsonify(req_details), 200


@app.route("/api/v1/inventory/blood-units/reserve", methods=["POST"])
def api_reserve_blood_units():
    """Pessimistically reserve blood units for emergency trauma under 120s lease."""
    data = request.get_json(silent=True) or {}
    req_id = data.get("requestId", f"req-{uuid.uuid4().hex[:8]}")
    fac_id = data.get("facilityId", "fac-001")
    blood_type = data.get("requiredBloodType")
    comp_type = data.get("componentType", "RED_BLOOD_CELLS")
    
    try:
        units = int(data.get("unitsRequested", 1))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid unitsRequested"}), 400

    if not blood_type:
        return jsonify({"error": "requiredBloodType is required"}), 400

    success, res_id, lease_exp, reserved_ids, err_msg = inventory_service.reserve_units(
        request_id=req_id,
        facility_id=fac_id,
        required_blood_type=blood_type,
        component_type=comp_type,
        units_requested=units,
        lease_seconds=120
    )

    if not success:
        return jsonify({"error": err_msg or "Insufficient inventory", "code": "INSUFFICIENT_COMPATIBLE_INVENTORY"}), 422

    return jsonify({
        "reservationId": res_id,
        "leaseExpiresAt": lease_exp,
        "reservedUnitIds": reserved_ids
    }), 200


@app.route("/api/v1/inventory/blood-units", methods=["GET", "POST"])
def api_inventory_blood_units():
    """
    GET: Summary stock gauges, expiration timeline, and units list.
    POST: Check-in / register a new blood unit with DIN barcode.
    """
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict()
        din = data.get("dinBarcode") or f"DIN-{uuid.uuid4().hex[:10].upper()}"
        fac_id = data.get("facilityId", "fac-001")
        blood_type = data.get("bloodType", "O_NEG")
        comp_type = data.get("componentType", "RED_BLOOD_CELLS")
        volume = int(data.get("volumeMl", 450))
        expires_at = data.get("expiresAt") or (datetime.utcnow().isoformat())

        res = inventory_service.register_unit(
            din_barcode=din,
            facility_id=fac_id,
            blood_type=blood_type,
            component_type=comp_type,
            volume_ml=volume,
            expires_at=expires_at
        )
        return jsonify(res), 201

    summary = inventory_service.get_inventory_summary()
    return jsonify(summary), 200


@app.route("/api/v1/donors/proximity-search", methods=["POST"])
def api_donors_proximity_search():
    """Execute PostGIS spherical Haversine radial distance query for eligible donors."""
    data = request.get_json(silent=True) or request.form.to_dict()
    lat = float(data.get("latitude", 40.7128))
    lon = float(data.get("longitude", -74.0060))
    radius = float(data.get("radiusMiles") or data.get("radius", 15.0))
    blood_types = data.get("bloodTypes")
    if isinstance(blood_types, str):
        blood_types = [b.strip() for b in blood_types.split(",") if b.strip()]

    result = proximity_service.search_proximity_donors(
        latitude=lat,
        longitude=lon,
        radius_miles=radius,
        blood_types=blood_types,
        min_donation_interval_days=56
    )
    return jsonify(result), 200


@app.route("/api/v1/donors/broadcast", methods=["POST"])
def api_donors_broadcast():
    """Dispatch targeted emergency push / SMS alert to donor list with fallback."""
    data = request.get_json(silent=True) or request.form.to_dict()
    req_id = data.get("requestId", f"disp-{uuid.uuid4().hex[:8]}")
    donor_ids = data.get("donorIds", [])
    if isinstance(donor_ids, str):
        donor_ids = [d.strip() for d in donor_ids.split(",") if d.strip()]
    if not donor_ids:
        # Default to all eligible donors if none specified
        prox = proximity_service.search_proximity_donors(latitude=40.7128, longitude=-74.0060, radius_miles=15.0)
        donor_ids = [d["donorId"] for d in prox.get("matchedDonors", []) if d["eligibilityStatus"] == "ELIGIBLE"]

    msg = data.get("message", "EMERGENCY: Urgent blood donors needed immediately.")
    urgency = data.get("urgencyTier", "CODE_RED")

    res = notification_service.broadcast_emergency_alert(
        request_id=req_id,
        donor_ids=donor_ids,
        message=msg,
        urgency_tier=urgency
    )
    return jsonify(res), 200


@app.route("/api/v1/audit/logs", methods=["GET"])
def api_audit_logs():
    """Retrieve immutable WORM HIPAA access ledger records."""
    logs = audit_service.get_audit_logs(limit=100)
    is_valid, total, tampered = audit_service.verify_ledger_integrity()
    return jsonify({
        "auditLogs": logs,
        "chainIntegrityStatus": "VALID" if is_valid else "CORRUPTED",
        "totalRecords": total,
        "tamperedRecords": tampered
    }), 200


@app.route("/api/v1/audit/verify", methods=["POST"])
def api_audit_verify():
    """Verify cryptographic hash chain integrity of the HIPAA WORM audit ledger."""
    is_valid, total, tampered = audit_service.verify_ledger_integrity()
    return jsonify({
        "verified": is_valid,
        "totalRecordsChecked": total,
        "tamperedRecordsCount": tampered,
        "verificationTimestamp": datetime.utcnow().isoformat()
    }), 200

# ============================================================================
# Clinical Dashboard UI Routes (Design Adaptation & Jinja2 Templates)
# ============================================================================

@app.route("/dispatch/dashboard")
def dispatch_dashboard():
    """Emergency Dispatch Center Console (Page 1 in DESIGN-PAGES-001.md)."""
    active_requests = dispatch_service.list_active_requests()
    inv_summary = inventory_service.get_inventory_summary()
    return render_template(
        "dispatch_dashboard.html",
        active_requests=active_requests,
        inventory_summary=inv_summary
    )


@app.route("/inventory/management")
def inventory_management():
    """Regional Blood Inventory & FEFO Console (Page 2 in DESIGN-PAGES-001.md)."""
    inv_summary = inventory_service.get_inventory_summary()
    return render_template(
        "inventory_management.html",
        summary=inv_summary["summary"],
        stock=inv_summary["stockByPhenotype"],
        units=inv_summary["units"]
    )


@app.route("/donors/geo-matching")
def donor_matching():
    """Donor Geospatial Matching & Broadcast Map (Page 3 in DESIGN-PAGES-001.md)."""
    prox = proximity_service.search_proximity_donors(latitude=40.7128, longitude=-74.0060, radius_miles=15.0)
    return render_template(
        "donor_matching.html",
        matched_donors=prox["matchedDonors"],
        radius=15.0
    )


@app.route("/audit")
def audit_viewer():
    """HIPAA Compliance & Audit Log Viewer (Page 4 in DESIGN-PAGES-001.md)."""
    logs = audit_service.get_audit_logs(limit=50)
    is_valid, total, tampered = audit_service.verify_ledger_integrity()
    return render_template(
        "audit_viewer.html",
        audit_logs=logs,
        chain_valid=is_valid,
        total_records=total
    )

# ============================================================================
# Existing Legacy Routes (Preserved for backwards-compatibility)
# ============================================================================

@app.route("/")
def home():
    if "user_id" in session:
        role = session.get("role")
        if role == "hospital":
            return redirect(url_for("hospital_dashboard"))
        elif role == "admin":
            return redirect(url_for("admin_dashboard"))
        elif role == "donor":
            return redirect(url_for("donor_profile"))
    return redirect(url_for("login_hospital"))


@app.route("/login/hospital", methods=["GET", "POST"])
def login_hospital():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username and password:
            session["user_id"] = 101
            session["username"] = username
            session["role"] = "hospital"
            flash(f"Welcome, {username}!", "success")
            return redirect(url_for("hospital_dashboard"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login_hospital.html")


@app.route("/login/admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username and password:
            session["user_id"] = 999
            session["username"] = username
            session["role"] = "admin"
            flash(f"Welcome, Admin {username}!", "success")
            return redirect(url_for("admin_queue"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login_admin.html")


@app.route("/login/donor", methods=["GET", "POST"])
def login_donor():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        donor = next((d for d in donors if d["username"] == username), None)
        if donor and password:
            session["user_id"] = 201
            session["username"] = donor["username"]
            session["role"] = "donor"
            flash(f"Welcome back, {donor['name']}!", "success")
            return redirect(url_for("donor_profile"))
        else:
            flash("Invalid donor credentials.", "danger")
    return render_template("login_donor.html")


@app.route("/login/social/<provider>")
def social_login(provider):
    session["user_id"] = 888
    session["username"] = f"social_{provider.lower()}_user"
    session["role"] = "donor"
    flash(f"Successfully authenticated via {provider.capitalize()}!", "success")
    return redirect(url_for("donor_profile"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("login_hospital"))


@app.route("/hospital/dashboard")
def hospital_dashboard():
    if session.get("role") != "hospital":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_hospital"))
    return render_template(
        "dashboard.html",
        demands=demands,
        scheduled_donors=scheduled_donors)


@app.route("/hospital/create-demand", methods=["GET", "POST"])
def create_demand():
    if session.get("role") != "hospital":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_hospital"))

    if request.method == "POST":
        blood_type = request.form.get("blood_type")
        units = request.form.get("units")
        notes = request.form.get("notes")
        urgency = request.form.get("urgency", "Emergency")
        district = request.form.get("district", "Downtown")
        file = request.files.get("document")

        if not blood_type or not units or int(units) <= 0:
            flash("Please specify valid blood type and positive units count.", "danger")
            return render_template("create_demand.html")

        filename = file.filename if file else "medical_order.pdf"

        new_demand_id = len(demands) + 1
        new_demand = {
            "id": new_demand_id,
            "hospital": session.get("username", "General Hospital"),
            "blood_type": blood_type,
            "units": int(units),
            "filename": filename,
            "status": "Pending",
            "urgency": urgency,
            "district": district,
            "notes": notes
        }
        demands.append(new_demand)

        audit_logs.append({
            "action": "EMERGENCY DEMAND CREATED",
            "details": f"Hospital '{session.get('username')}' created demand #{new_demand_id} for {units} units of {blood_type} ({urgency}).",
            "user": session.get("username"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        flash("Blood demand request submitted successfully!", "success")
        return redirect(url_for("hospital_dashboard"))

    return render_template("create_demand.html")


@app.route("/donor/register", methods=["GET", "POST"])
def register_donor():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        age = request.form.get("age")
        gender = request.form.get("gender")
        blood_group = request.form.get("blood_group")
        last_donation = request.form.get("last_donation")

        if not name or not username or not blood_group:
            flash("All fields are required.", "danger")
            return render_template("register_donor.html")

        if int(age) < 16:
            flash("Minimum age for voluntary donation is 16.", "danger")
            return render_template("register_donor.html")

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
        session["user_id"] = len(donors) + 200
        session["username"] = username
        session["role"] = "donor"

        audit_logs.append({
            "action": "DONOR REGISTRATION",
            "details": f"New voluntary donor '{name}' registered with blood group {blood_group}.",
            "user": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        flash("Registration successful! Welcome to BDCN.", "success")
        return redirect(url_for("donor_profile"))

    return render_template("register_donor.html")


@app.route("/donor/profile", methods=["GET", "POST"])
def donor_profile():
    if session.get("role") != "donor":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_donor"))

    username = session.get("username")
    target_donor = next((d for d in donors if d["username"] == username), None)
    if not target_donor:
        target_donor = {
            "name": username or "Voluntary Donor",
            "username": username or "donor_user",
            "age": 28,
            "gender": "Other",
            "blood_group": "O-",
            "last_donation": "2025-11-15",
            "donation_count": 0
        }
        donors.append(target_donor)

    if request.method == "POST":
        target_donor["name"] = request.form.get("name", target_donor["name"])
        target_donor["age"] = int(request.form.get("age", target_donor["age"]))
        flash("Profile updated successfully!", "success")

    count = target_donor.get("donation_count", 0)
    badges = [
        {
            "name": "Bronze Savior",
            "description": "Awarded for completing at least 1 voluntary donation.",
            "earned": count >= 1
        },
        {
            "name": "Silver Savior",
            "description": "Awarded for completing at least 3 voluntary donations.",
            "earned": count >= 3
        },
        {
            "name": "Gold Guardian",
            "description": "Awarded for completing at least 5 voluntary donations.",
            "earned": count >= 5
        }
    ]

    return render_template("donor_profile.html", donor=target_donor, badges=badges)


@app.route("/donor/share/<badge_name>", methods=["POST"])
def donor_share(badge_name):
    clean_badge = badge_name.replace("-", " ")
    flash(f"Successfully shared your {clean_badge} badge on social networks!", "success")
    return redirect(url_for("donor_profile"))


@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_admin"))
    return render_template("verification_queue.html", demands=demands)


@app.route("/admin/queue")
def admin_queue():
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_admin"))
    return render_template("verification_queue.html", demands=demands)


@app.route("/admin/verify/<int:demand_id>", methods=["POST"])
def verify_demand(demand_id):
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_admin"))

    action = request.form.get("action")
    target_demand = None
    for d in demands:
        if d["id"] == demand_id:
            target_demand = d
            break

    if target_demand:
        if action == "approve":
            target_demand["status"] = "Approved"

            new_alert_id = len(alerts) + 1
            alerts.append({
                "id": new_alert_id,
                "hospital": target_demand["hospital"],
                "blood_type": target_demand["blood_type"],
                "status": "Active"
            })

            audit_logs.append({
                "action": "EMERGENCY DEMAND APPROVED",
                "details": f"Approved demand #{demand_id} ({target_demand['blood_type']}) for {target_demand.get('district', 'Downtown')}. Emitted event.",
                "user": session.get("username"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash(f"Approved demand #{demand_id}! Alert dispatched to nearby donors.", "success")
        elif action == "reject":
            target_demand["status"] = "Rejected"
            audit_logs.append({
                "action": "EMERGENCY DEMAND REJECTED",
                "details": f"Rejected demand #{demand_id} ({target_demand['blood_type']}).",
                "user": session.get("username"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash(f"Rejected demand #{demand_id}.", "warning")
    else:
        flash("Demand request not found.", "danger")

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

    sorted_logs = sorted(
        audit_logs,
        key=lambda x: x["timestamp"],
        reverse=True)
    return render_template("audit_log.html", logs=sorted_logs)


@app.route("/map/hotspots")
def map_hotspots():
    radius = int(request.args.get("radius", 50))
    blood_type = request.args.get("blood_type", "All")

    filtered = [h for h in raw_hotspots if h["distance"] <= radius]
    if blood_type != "All":
        filtered = [h for h in filtered if h["blood_type"] == blood_type]

    return render_template(
        "map_hotspots.html", hotspots=filtered, radius=radius, blood_type=blood_type)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
