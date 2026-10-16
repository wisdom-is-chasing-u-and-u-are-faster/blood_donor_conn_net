# This is a Flask web application for a Blood Donor Connection Network.
# It provides functionalities for hospitals to request blood,
# administrators to manage and approve these requests, and
# voluntary donors to receive emergency broadcasts, respond in real time,
# and receive digital check-in passes.
import os
import uuid
from datetime import datetime, timedelta
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    url_for,
    jsonify
)

# Initialize database schema and seeds
try:
    from db.init_db import init_database, get_connection
    init_database()
except Exception:
    get_connection = None

app = Flask(__name__, static_folder="public", static_url_path="/public")
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "super-secret-bdcn-key-12345")

# In-memory mock databases
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
        "donor_id": "DN-A8C4-E02B",
        "age": 28,
        "gender": "Female",
        "blood_group": "O-",
        "last_donation": "2025-11-15",
        "donation_count": 5
    },
    {
        "name": "John Doe",
        "username": "johndoe",
        "donor_id": "DN-B192-F93C",
        "age": 34,
        "gender": "Male",
        "blood_group": "A+",
        "last_donation": "2025-08-20",
        "donation_count": 2
    }
]

# Emergency Requisitions (HL7 FHIR & REST Store)
emergency_requisitions = [
    {
        "request_id": "REQ-EMERG-2026-001",
        "hospital_id": "HOSP-001",
        "hospital_name": "City General Hospital",
        "hospital_address": "City General Hospital (123 Health St.)",
        "blood_type": "O-",
        "units": 4,
        "urgency": "Emergency",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "radius_km": 15.0,
        "status": "broadcast",
        "notes": "Acute trauma resuscitation Code Red",
        "created_at": "2026-10-16 14:00:00"
    }
]

donor_responses_store = [
    {
        "response_id": "RESP-2026-001",
        "request_id": "REQ-EMERG-2026-001",
        "donor_id": "DN-A8C4-E02B",
        "donor_username": "janesmith",
        "action": "confirmed",
        "responded_at": "2026-10-16 14:02:15"
    }
]

digital_passes_store = [
    {
        "pass_id": "PASS-2026-A8C4",
        "response_id": "RESP-2026-001",
        "request_id": "REQ-EMERG-2026-001",
        "donor_id": "DN-A8C4-E02B",
        "hospital_name": "City General Hospital",
        "hospital_address": "City General Hospital (123 Health St.)",
        "blood_type": "O-",
        "appointment_time": "October 26, 2024 at 3:45 PM",
        "qr_code_data": "BDCN:PASS:PASS-2026-A8C4:DN-A8C4-E02B:O-:EXP-45M",
        "status": "ACTIVE"
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
# HEALTH & READINESS PROBE
# ============================================================================
@app.route("/health")
def health_check():
    """Readiness probe for container orchestration."""
    return jsonify({
        "status": "healthy",
        "service": "blood_donor_conn_net",
        "timestamp": datetime.now().isoformat()
    }), 200


# ============================================================================
# REST / FHIR CLINICAL REQUISITION ENDPOINTS (REQ-F-001, REQ-F-008, AC 4)
# ============================================================================
@app.route("/api/v1/clinical/emergency-requests", methods=["GET", "POST"])
def api_clinical_emergency_requests():
    """
    POST: Ingests clinical emergency requisitions (HL7 FHIR SupplyRequest format or JSON).
    GET: Lists all active emergency requisitions.
    """
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        if not isinstance(data, dict):
            data = {}

        hospital_val = data.get("hospital")
        hospital_display = (
            hospital_val.get("display") if isinstance(hospital_val, dict)
            else (str(hospital_val) if hospital_val else None)
        )
        hospital_name = (
            data.get("hospital_name") or
            hospital_display or
            "City General Hospital"
        )
        hospital_id = data.get("hospital_id") or data.get("id") or f"HOSP-{uuid.uuid4().hex[:6].upper()}"
        blood_type = data.get("blood_type") or data.get("bloodType") or "O-"

        qty_val = data.get("quantity")
        qty_num = (
            qty_val.get("value") if isinstance(qty_val, dict)
            else (int(qty_val) if str(qty_val).isdigit() else None)
        )
        try:
            units = int(data.get("units") or qty_num or 4)
        except (ValueError, TypeError):
            units = 4

        urgency = data.get("urgency") or data.get("priority") or "Emergency"
        notes = data.get("notes") or "Clinical emergency requisition"
        try:
            radius_km = float(data.get("radius_km") or 15.0)
        except (ValueError, TypeError):
            radius_km = 15.0

        try:
            lat = float(data.get("latitude") or 37.7749)
            lng = float(data.get("longitude") or -122.4194)
        except (ValueError, TypeError):
            lat, lng = 37.7749, -122.4194

        request_id = f"REQ-EMERG-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        new_req = {
            "request_id": request_id,
            "hospital_id": hospital_id,
            "hospital_name": hospital_name,
            "hospital_address": f"{hospital_name} (123 Health St.)",
            "blood_type": blood_type,
            "units": units,
            "urgency": urgency,
            "latitude": lat,
            "longitude": lng,
            "radius_km": radius_km,
            "status": "broadcast",
            "notes": notes,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        emergency_requisitions.insert(0, new_req)

        # Match proximate voluntary donors
        matched_donors = [d for d in donors if d.get("blood_group") == blood_type or blood_type == "O-"]
        matched_count = len(matched_donors) if matched_donors else 1

        # Emit audit log and alert
        audit_logs.append({
            "action": "FHIR EMERGENCY REQUISITION INGESTED",
            "details": f"Ingested {request_id} for {blood_type} ({units} units) at {hospital_name}. Broadcast to {matched_count} donors.",
            "user": hospital_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        alerts.append({
            "id": len(alerts) + 1,
            "hospital": hospital_name,
            "blood_type": blood_type,
            "status": "Active"
        })

        return jsonify({
            "request_id": request_id,
            "status": "broadcast",
            "matched_donors_count": matched_count,
            "created_at": new_req["created_at"],
            "message": "Emergency requisition ingested and broadcasted successfully."
        }), 201

    # GET: List active emergency requisitions
    return jsonify({
        "status": "success",
        "count": len(emergency_requisitions),
        "requests": emergency_requisitions
    }), 200


@app.route("/api/v1/clinical/emergency-requests/<request_id>", methods=["GET"])
def api_get_emergency_request(request_id):
    """Retrieve details for a specific emergency requisition."""
    req = next((r for r in emergency_requisitions if r["request_id"] == request_id), None)
    if not req:
        return jsonify({"error": "Emergency requisition not found"}), 404
    return jsonify(req), 200


# ============================================================================
# REST DONOR EMERGENCY RESPONSES & DIGITAL PASSES (REQ-F-005, REQ-F-009, AC 1, 2, 3)
# ============================================================================
@app.route("/api/v1/donors/emergency-responses", methods=["POST"])
def api_donor_emergency_response():
    """
    Submit voluntary donor response (confirm/decline) to an active emergency request.
    Generates time-sensitive digital check-in pass upon confirmation.
    """
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    if not isinstance(data, dict):
        data = {}
    request_id = data.get("request_id") or (emergency_requisitions[0]["request_id"] if emergency_requisitions else "REQ-EMERG-2026-001")
    donor_id = data.get("donor_id") or session.get("donor_id") or "DN-A8C4-E02B"
    action = data.get("action", "confirmed").lower()

    target_req = next((r for r in emergency_requisitions if r["request_id"] == request_id), None)
    hospital_name = target_req["hospital_name"] if target_req else "City General Hospital"
    hospital_address = target_req.get("hospital_address", f"{hospital_name} (123 Health St.)")
    blood_type = target_req["blood_type"] if target_req else "O-"

    response_id = f"RESP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    pass_id = f"PASS-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    app_time = (datetime.now() + timedelta(minutes=45)).strftime("%B %d, %Y at %I:%M %p")
    qr_code = f"BDCN:PASS:{pass_id}:{donor_id}:{blood_type}:EXP-45M"

    new_response = {
        "response_id": response_id,
        "request_id": request_id,
        "donor_id": donor_id,
        "donor_username": session.get("username", "janesmith"),
        "action": action,
        "responded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    donor_responses_store.insert(0, new_response)

    if action == "confirmed":
        new_pass = {
            "pass_id": pass_id,
            "response_id": response_id,
            "request_id": request_id,
            "donor_id": donor_id,
            "hospital_name": hospital_name,
            "hospital_address": hospital_address,
            "blood_type": blood_type,
            "appointment_time": app_time,
            "qr_code_data": qr_code,
            "status": "ACTIVE",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        digital_passes_store.insert(0, new_pass)

        audit_logs.append({
            "action": "DONOR PARTICIPATION CONFIRMED",
            "details": f"Donor {donor_id} confirmed response to {request_id}. Issued pass {pass_id}.",
            "user": donor_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        return jsonify({
            "status": "confirmed",
            "response_id": response_id,
            "check_in_pass_id": pass_id,
            "appointment_time": app_time,
            "qr_code_data": qr_code,
            "message": "Participation confirmed! Check-in pass generated."
        }), 200
    else:
        audit_logs.append({
            "action": "DONOR PARTICIPATION DECLINED",
            "details": f"Donor {donor_id} declined emergency request {request_id}.",
            "user": donor_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return jsonify({
            "status": "declined",
            "response_id": response_id,
            "message": "Response recorded. Thank you for your feedback."
        }), 200


@app.route("/api/v1/donors/check-in-pass/<pass_id>", methods=["GET"])
def api_get_check_in_pass(pass_id):
    """Retrieve digital check-in pass details by pass ID."""
    pass_obj = next((p for p in digital_passes_store if p["pass_id"] == pass_id), None)
    if not pass_obj:
        return jsonify({"error": "Pass not found"}), 404
    return jsonify(pass_obj), 200


# ============================================================================
# DONOR PORTAL UI ROUTES (WCAG 2.1 AA COMPLIANT, VARIANT A DESIGNS)
# ============================================================================
@app.route("/donor/portal/login", methods=["GET", "POST"])
def donor_portal_login():
    """Secure Donor Portal login view."""
    if request.method == "POST":
        username = request.form.get("username", "janesmith")
        target = next((d for d in donors if d["username"] == username), None)
        session["username"] = username
        session["role"] = "donor"
        session["donor_id"] = target.get("donor_id", "DN-A8C4-E02B") if target else "DN-A8C4-E02B"
        flash(f"Welcome to the Secure Donor Portal, {username}!", "success")
        return redirect(url_for("donor_portal_emergency_response"))
    return render_template("donor_portal_login.html")


@app.route("/donor/portal/emergency-response", methods=["GET"])
def donor_portal_emergency_response():
    """Emergency response screen showing broadcast details and instant actions."""
    latest_req = emergency_requisitions[0] if emergency_requisitions else {
        "request_id": "REQ-EMERG-2026-001",
        "hospital_name": "City General Hospital",
        "hospital_address": "City General Hospital (123 Health St.)",
        "blood_type": "O-",
        "units": 4,
        "urgency": "Emergency",
        "radius_km": 15.0,
        "notes": "Code Red emergency resuscitation"
    }
    return render_template("donor_emergency_response.html", requisition=latest_req)


@app.route("/donor/portal/respond", methods=["POST"])
def donor_portal_respond():
    """Handles donor confirm/decline button action from web UI."""
    action = request.form.get("action", "confirmed")
    request_id = request.form.get("request_id", "REQ-EMERG-2026-001")
    donor_id = session.get("donor_id", "DN-A8C4-E02B")

    if action == "confirmed":
        pass_id = f"PASS-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        app_time = (datetime.now() + timedelta(minutes=45)).strftime("%B %d, %Y at %I:%M %p")
        target_req = next((r for r in emergency_requisitions if r["request_id"] == request_id), None)
        blood_type = target_req["blood_type"] if target_req else "O-"
        hosp_addr = target_req.get("hospital_address", "City General Hospital (123 Health St.)") if target_req else "City General Hospital (123 Health St.)"

        new_pass = {
            "pass_id": pass_id,
            "response_id": f"RESP-{uuid.uuid4().hex[:6].upper()}",
            "request_id": request_id,
            "donor_id": donor_id,
            "hospital_name": target_req["hospital_name"] if target_req else "City General Hospital",
            "hospital_address": hosp_addr,
            "blood_type": blood_type,
            "appointment_time": app_time,
            "qr_code_data": f"BDCN:PASS:{pass_id}:{donor_id}:{blood_type}:EXP-45M",
            "status": "ACTIVE",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        digital_passes_store.insert(0, new_pass)
        flash("Thank you for confirming! Your digital check-in pass has been generated.", "success")
        return redirect(url_for("donor_portal_check_in_pass"))
    else:
        flash("Thank you for your response. We will alert you on the next emergency request.", "warning")
        return redirect(url_for("donor_portal_emergency_response"))


@app.route("/donor/portal/check-in-pass", methods=["GET"])
def donor_portal_check_in_pass():
    """Digital reception check-in pass view with dynamic QR code."""
    latest_pass = digital_passes_store[0] if digital_passes_store else {
        "pass_id": "PASS-2026-A8C4",
        "donor_id": "DN-A8C4-E02B",
        "hospital_address": "City General Hospital (123 Health St.)",
        "appointment_time": "October 26, 2024 at 3:45 PM",
        "blood_type": "O-Negative",
        "qr_code_data": "BDCN:PASS:PASS-2026-A8C4:DN-A8C4-E02B:O-:EXP-45M"
    }
    return render_template("donor_check_in_pass.html", pass_details=latest_pass)


# Mockup parity static redirects
@app.route("/login.html")
def mockup_login():
    return redirect(url_for("donor_portal_login"))


@app.route("/emergency_response.html")
def mockup_emergency():
    return redirect(url_for("donor_portal_emergency_response"))


@app.route("/check_in_pass.html")
def mockup_pass():
    return redirect(url_for("donor_portal_check_in_pass"))


# ============================================================================
# EXISTING BDCN ROUTES (HOSPITAL, DONOR, ADMIN PORTALS)
# ============================================================================
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

        target_donor = next(
            (d for d in donors if d["username"] == username), None)
        if target_donor and password:
            session["username"] = username
            session["role"] = "donor"
            session["donor_id"] = target_donor.get("donor_id", "DN-A8C4-E02B")
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
            "donor_id": f"DN-{uuid.uuid4().hex[:8].upper()}",
            "age": 25,
            "gender": "Other",
            "blood_group": "O+",
            "last_donation": None,
            "donation_count": 1
        }
        donors.append(target_donor)

    session["username"] = username
    session["role"] = "donor"
    session["donor_id"] = target_donor.get("donor_id")

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
            "donor_id": f"DN-{uuid.uuid4().hex[:8].upper()}",
            "age": int(age),
            "gender": gender,
            "blood_group": blood_group,
            "last_donation": last_donation,
            "donation_count": 0
        }
        donors.append(new_donor)

        audit_logs.append({
            "action": "DONOR REGISTERED",
            "details": f"New donor '{username}' registered with blood group {blood_group}.",
            "user": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        session["username"] = username
        session["role"] = "donor"
        session["donor_id"] = new_donor["donor_id"]
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

    return render_template("donor_profile.html",
                           donor=target_donor, badges=badges, history=history)


@app.route("/donor/share/<badge_name>", methods=["POST"])
def share_badge(badge_name):
    if session.get("role") != "donor":
        flash("Unauthorized.", "danger")
        return redirect(url_for("login_donor"))

    username = session.get("username")
    clean_badge = badge_name.replace("-", " ")

    audit_logs.append({
        "action": "BADGE SHARED",
        "details": f"Donor '{username}' shared their achievement '{clean_badge}' to social media.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
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
            audit_logs.append({
                "action": "ADMIN LOGIN",
                "details": f"Administrator '{username}' logged in successfully.",
                "user": username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash("Logged in to Administrator Portal successfully!", "success")
            return redirect(url_for("admin_queue"))
        flash("Invalid credentials.", "danger")
    return render_template("login_admin.html")


@app.route("/logout")
def logout():
    username = session.get("username", "Unknown")
    session.clear()
    audit_logs.append({
        "action": "USER LOGOUT",
        "details": f"User '{username}' logged out.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    flash("Logged out successfully.", "info")
    return redirect(url_for("login_hospital"))


@app.route("/hospital/dashboard")
def hospital_dashboard():
    if session.get("role") != "hospital" and session.get("role") != "donor":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_hospital"))

    h_demands = [d for d in demands]
    return render_template("dashboard.html", demands=h_demands,
                           scheduled_donors=scheduled_donors)


@app.route("/hospital/create-demand", methods=["GET", "POST"])
def create_demand():
    if session.get("role") != "hospital":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_hospital"))

    if request.method == "POST":
        blood_type = request.form.get("blood_type")
        units = request.form.get("units")
        file = request.files.get("document")
        notes = request.form.get("notes", "")
        urgency = request.form.get("urgency", "Emergency")
        district = request.form.get("district", "Downtown")

        if not blood_type or not units or not file:
            flash("All fields including compliance document upload are required.", "danger")
            return redirect(url_for("create_demand"))

        filename = file.filename
        new_id = len(demands) + 1
        new_demand = {
            "id": new_id,
            "hospital": session.get("username"),
            "blood_type": blood_type,
            "units": int(units),
            "filename": filename,
            "status": "Pending",
            "urgency": urgency,
            "district": district
        }
        demands.append(new_demand)

        audit_logs.append({
            "action": "BLOOD DEMAND CREATED",
            "details": f"Demand #{new_id} ({blood_type}, {units} units) created for {district} with urgency {urgency}. File: {filename}. Notes: {notes}",
            "user": session.get("username"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        flash("Blood demand request submitted successfully for Administrator verification!", "success")
        return redirect(url_for("hospital_dashboard"))

    return render_template("create_demand.html")


@app.route("/admin/queue")
def admin_queue():
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_admin"))

    filter_district = request.args.get("filter_district", "All")
    pending_demands = [d for d in demands if d["status"] == "Pending"]
    if filter_district != "All":
        pending_demands = [d for d in pending_demands if d.get("district") == filter_district]

    return render_template("verification_queue.html",
                           pending_demands=pending_demands, filter_district=filter_district)


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
    debug_flag = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1")
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=debug_flag)
