# This is a Flask web application for the Blood Donor Connection Network (BDCN).
# It provides functionalities for hospitals, donors, recipients, and administrators.
# The application supports 12-factor configuration, RESTful APIs, and full-fidelity UI templates.
import os
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, session,
    flash, url_for, jsonify, send_from_directory
)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="public",
    static_url_path="/static"
)

# 12-Factor Environment Configuration
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "super-secret-bdcn-key-12345"
)
PORT = int(os.environ.get("PORT", 5000))
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://bdcn_user:bdcn_password@localhost:5432/bdcn_db"
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
FLASK_ENV = os.environ.get("FLASK_ENV", "development")

# In-memory mock database entities
demands = [
    {
        "id": 1,
        "hospital": "General Hospital",
        "blood_type": "A+",
        "units": 10,
        "filename": "compliance_doc_A.pdf",
        "status": "Approved",
        "urgency": "Critical",
        "district": "Downtown",
        "created_at": "2026-10-14 10:00:00"
    },
    {
        "id": 2,
        "hospital": "General Hospital",
        "blood_type": "O-",
        "units": 4,
        "filename": "compliance_doc_B.pdf",
        "status": "Pending",
        "urgency": "High",
        "district": "North District",
        "created_at": "2026-10-14 10:30:00"
    },
    {
        "id": 3,
        "hospital": "City Clinic",
        "blood_type": "B+",
        "units": 2,
        "filename": "requisition_doc_C.pdf",
        "status": "Pending",
        "urgency": "Medium",
        "district": "East Valley",
        "created_at": "2026-10-14 11:15:00"
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
        "details": "BDCN Core Platform service started with 12-factor configuration.",
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

# Registered donors with gamification metrics
donors = [
    {
        "name": "Jane Smith",
        "username": "janesmith",
        "age": 28,
        "gender": "Female",
        "blood_group": "O-",
        "last_donation": "2025-11-15",
        "donation_count": 5,
        "total_points": 1250,
        "lives_impacted": 5
    },
    {
        "name": "John Doe",
        "username": "johndoe",
        "age": 34,
        "gender": "Male",
        "blood_group": "A+",
        "last_donation": "2025-08-20",
        "donation_count": 2,
        "total_points": 450,
        "lives_impacted": 2
    }
]

# Mock donor density hotspots with privacy-preserving coarse centroid coordinates (REQ-F-010, REQ-N-001)
raw_hotspots = [
    {"district": "Downtown", "count": 24, "blood_type": "O-", "distance": 8,
     "latitude_coarse": 37.77, "longitude_coarse": -122.42},
    {"district": "North District", "count": 15, "blood_type": "A+", "distance": 12,
     "latitude_coarse": 37.80, "longitude_coarse": -122.40},
    {"district": "East Valley", "count": 8, "blood_type": "B+", "distance": 22,
     "latitude_coarse": 37.75, "longitude_coarse": -122.35},
    {"district": "South Coast", "count": 19, "blood_type": "O+", "distance": 15,
     "latitude_coarse": 37.70, "longitude_coarse": -122.45},
    {"district": "West Hills", "count": 11, "blood_type": "AB-", "distance": 35,
     "latitude_coarse": 37.82, "longitude_coarse": -122.50}
]

districts_registry = [
    {"name": "Downtown", "available_donors": 24, "distance_km": 8},
    {"name": "North District", "available_donors": 15, "distance_km": 12},
    {"name": "South Coast", "available_donors": 19, "distance_km": 15},
    {"name": "East Valley", "available_donors": 8, "distance_km": 22},
    {"name": "West Hills", "available_donors": 11, "distance_km": 35}
]


# ==========================================
# 0. Health Check Probe & Static Fallback
# ==========================================

@app.route("/health")
def health_check():
    """Service health and container readiness probe."""
    return jsonify({
        "status": "ok",
        "service": "bdcn-core-platform",
        "environment": FLASK_ENV,
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static assets from static or public directory."""
    static_dir = os.path.join(app.root_path, "static")
    if os.path.exists(os.path.join(static_dir, filename)):
        return send_from_directory(static_dir, filename)
    public_dir = os.path.join(app.root_path, "public")
    return send_from_directory(public_dir, filename)


# ==========================================
# 1. Core Navigation & Authentication Pages
# ==========================================

@app.route("/")
def home():
    if "username" in session:
        if session.get("role") == "hospital":
            return redirect(url_for("hospital_dashboard"))
        elif session.get("role") == "admin":
            return redirect(url_for("admin_queue"))
        elif session.get("role") == "donor":
            return redirect(url_for("donor_dashboard_view"))
        elif session.get("role") == "recipient":
            return redirect(url_for("recipient_discovery_map_view"))
    return redirect(url_for("login_hospital"))


@app.route("/overview")
@app.route("/index.html")
def platform_overview():
    """Full prototype overview mounting all portals."""
    return render_template("index.html")


@app.route("/role-selection")
def role_selection_view():
    """Interactive role selection view (Donor vs Recipient)."""
    return render_template("role_selection.html")


@app.route("/login-registration")
def login_registration_view():
    """Unified onboarding and social login portal."""
    return render_template("login_registration.html")


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
    """Mock social media authentication (Google, Apple, Facebook) - REQ-F-008, AC 1."""
    valid_providers = ["google", "apple", "facebook"]
    prov = provider.lower()
    if prov not in valid_providers:
        prov = "google"

    username = f"social_{prov}_user"
    name = f"Social {prov.capitalize()} User"

    target_donor = next((d for d in donors if d["username"] == username), None)
    if not target_donor:
        target_donor = {
            "name": name,
            "username": username,
            "age": 25,
            "gender": "Other",
            "blood_group": "O+",
            "last_donation": "2025-10-01",
            "donation_count": 1,
            "total_points": 250,
            "lives_impacted": 1
        }
        donors.append(target_donor)

    session["username"] = username
    session["role"] = "donor"

    audit_logs.append({
        "action": "SOCIAL LOGIN",
        "details": f"User logged in via {prov.capitalize()}.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    flash(f"Successfully authenticated via {prov.capitalize()}!", "success")
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
            "donation_count": 0,
            "total_points": 100,
            "lives_impacted": 0
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
        flash("Registration successful! Welcome to the BDCN family.", "success")
        return redirect(url_for("donor_profile"))

    return render_template("register_donor.html")


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


# ==========================================
# 2. Recipient Request Intake & Discovery Map
# ==========================================

@app.route("/recipient/request", methods=["GET", "POST"])
def recipient_request_view():
    """Create blood donation request with medical necessity upload (REQ-F-003, AC 3)."""
    if request.method == "POST":
        blood_type = request.form.get("blood_type")
        units = request.form.get("units", 1)
        urgency = request.form.get("urgency", "Medium")
        district = request.form.get("district", "Downtown")
        notes = request.form.get("notes", "")
        file = request.files.get("document")

        if not blood_type:
            flash("Blood group selection is required.", "danger")
            return redirect(url_for("recipient_request_view"))

        filename = file.filename if file else "uploaded_prescription.pdf"
        new_id = len(demands) + 1
        username = session.get("username", "Recipient Advocate")

        new_demand = {
            "id": new_id,
            "hospital": username,
            "blood_type": blood_type,
            "units": int(units),
            "filename": filename,
            "status": "Pending",
            "urgency": urgency,
            "district": district,
            "notes": notes,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        demands.append(new_demand)

        audit_logs.append({
            "action": "BLOOD REQUISITION SUBMITTED",
            "details": (
                f"Requisition #{new_id} ({blood_type}, {units} units, {urgency}) "
                f"submitted for {district}. Document: {filename}"
            ),
            "user": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        flash("Blood donation request submitted successfully! Requisition is active.", "success")
        return redirect(url_for("recipient_discovery_map_view"))

    return render_template("recipient_request_form.html")


@app.route("/recipient/discovery-map")
@app.route("/map/hotspots")
def recipient_discovery_map_view():
    """Map of donor hotspots with proximity radius and district fallback (REQ-F-009, REQ-F-011, AC 2)."""
    radius = int(request.args.get("radius", 50))
    blood_type = request.args.get("blood_type", "All")

    filtered = [h for h in raw_hotspots if h["distance"] <= radius]
    if blood_type != "All":
        filtered = [h for h in filtered if h["blood_type"] == blood_type]

    return render_template(
        "donor_discovery_map.html",
        hotspots=filtered,
        radius=radius,
        blood_type=blood_type
    )


# ==========================================
# 3. Donor Dashboard & Gamification Engine
# ==========================================

def _get_donor_badges(donation_count):
    return [
        {
            "name": "Bronze Savior",
            "description": "Awarded for completing at least 1 voluntary donation.",
            "earned": donation_count >= 1
        },
        {
            "name": "Silver Savior",
            "description": "Awarded for completing at least 3 voluntary donations.",
            "earned": donation_count >= 3
        },
        {
            "name": "Gold Guardian",
            "description": "Awarded for completing at least 5 voluntary donations.",
            "earned": donation_count >= 5
        }
    ]


@app.route("/donor/dashboard")
def donor_dashboard_view():
    """Donor dashboard displaying impact, badges, and active donation requests (AC 4)."""
    username = session.get("username", "janesmith")
    target_donor = next((d for d in donors if d["username"] == username), donors[0])

    count = target_donor.get("donation_count", 5)
    badges = _get_donor_badges(count)

    history = [
        {"location": "City General Hospital", "date": "2025-11-15", "units": 1},
        {"location": "Community Blood Drive", "date": "2025-08-20", "units": 1}
    ]

    # Active blood requests list (AC 4)
    active_requests = [d for d in demands if d.get("status") in ["Approved", "Pending"]]

    return render_template(
        "donor_dashboard.html",
        donor=target_donor,
        badges=badges,
        history=history,
        active_requests=active_requests
    )


@app.route("/donor/profile")
def donor_profile():
    """Donor profile route (retains backward compatibility)."""
    if session.get("role") != "donor" and "username" not in session:
        session["username"] = "janesmith"
        session["role"] = "donor"

    username = session.get("username")
    target_donor = next((d for d in donors if d["username"] == username), donors[0])

    count = target_donor.get("donation_count", 0)
    badges = _get_donor_badges(count)

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

    return render_template(
        "donor_profile.html",
        donor=target_donor,
        badges=badges,
        history=history
    )


@app.route("/profile/gamification")
def profile_gamification_view():
    """Profile and gamification progression page (REQ-F-002)."""
    username = session.get("username", "janesmith")
    target_donor = next((d for d in donors if d["username"] == username), donors[0])

    gamification_data = {
        "total_points": target_donor.get("total_points", 1250),
        "lives_impacted": target_donor.get("lives_impacted", 5)
    }

    return render_template(
        "profile_gamification.html",
        donor=target_donor,
        gamification=gamification_data
    )


@app.route("/notifications")
def notifications_view():
    """Encrypted clinical notification center (REQ-F-006)."""
    return render_template("secure_notification_center.html")


@app.route("/donor/share/<badge_name>", methods=["POST"])
def share_badge(badge_name):
    """Badge social sharing API (REQ-F-007)."""
    username = session.get("username", "voluntary_donor")
    clean_badge = badge_name.replace("-", " ")

    audit_logs.append({
        "action": "BADGE SHARED",
        "details": f"Donor '{username}' shared achievement '{clean_badge}' to social media.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    flash(f"Successfully shared your {clean_badge} badge to your social profiles!", "success")
    return redirect(request.referrer or url_for("donor_dashboard_view"))


# ==========================================
# 4. Hospital & Admin Portals
# ==========================================

@app.route("/hospital/dashboard")
def hospital_dashboard():
    h_demands = [d for d in demands]
    return render_template("dashboard.html", demands=h_demands, scheduled_donors=scheduled_donors)


@app.route("/hospital/create-demand", methods=["GET", "POST"])
def create_demand():
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
            "hospital": session.get("username", "Hospital"),
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
            "action": "BLOOD DEMAND CREATED",
            "details": f"Demand #{new_id} ({blood_type}, {units} units) created for {district}. File: {filename}",
            "user": session.get("username", "Hospital"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        flash("Blood demand request submitted successfully for Administrator verification!", "success")
        return redirect(url_for("hospital_dashboard"))

    return render_template("create_demand.html")


@app.route("/admin/queue")
def admin_queue():
    filter_district = request.args.get("filter_district", "All")
    pending_demands = [d for d in demands if d["status"] == "Pending"]
    if filter_district != "All":
        pending_demands = [d for d in pending_demands if d.get("district") == filter_district]

    return render_template("verification_queue.html", pending_demands=pending_demands, filter_district=filter_district)


@app.route("/admin/verify/<int:demand_id>", methods=["POST"])
def verify_demand(demand_id):
    action = request.form.get("action")
    target_demand = next((d for d in demands if d["id"] == demand_id), None)

    if target_demand:
        if action == "approve":
            target_demand["status"] = "Approved"
            alerts.append({
                "id": len(alerts) + 1,
                "hospital": target_demand["hospital"],
                "blood_type": target_demand["blood_type"],
                "status": "Active"
            })
            audit_logs.append({
                "action": "EMERGENCY DEMAND APPROVED",
                "details": f"Approved demand #{demand_id} ({target_demand['blood_type']}). Emitted event.",
                "user": session.get("username", "admin"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash(f"Approved demand #{demand_id}! Alert dispatched to nearby donors.", "success")
        elif action == "reject":
            target_demand["status"] = "Rejected"
            audit_logs.append({
                "action": "EMERGENCY DEMAND REJECTED",
                "details": f"Rejected demand #{demand_id} ({target_demand['blood_type']}).",
                "user": session.get("username", "admin"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash(f"Rejected demand #{demand_id}.", "warning")
    else:
        flash("Demand request not found.", "danger")

    return redirect(url_for("admin_queue"))


@app.route("/admin/alerts")
def admin_alerts():
    return render_template("alert_management.html", alerts=alerts)


@app.route("/admin/audit-log")
def admin_audit_log():
    sorted_logs = sorted(audit_logs, key=lambda x: x["timestamp"], reverse=True)
    return render_template("audit_log.html", logs=sorted_logs)


# ==========================================
# 5. RESTful API v1 Endpoints (api_contract)
# ==========================================

@app.route("/api/v1/auth/social/<provider>", methods=["GET"])
def api_social_auth(provider):
    """API endpoint for mock OAuth authentication (REQ-F-008, AC 1)."""
    prov = provider.lower()
    username = f"social_{prov}_user"
    name = f"Social {prov.capitalize()} User"

    return jsonify({
        "status": "authenticated",
        "provider": prov,
        "user": {
            "username": username,
            "name": name,
            "role": "donor"
        }
    }), 200


@app.route("/api/v1/donors/hotspots", methods=["GET"])
def api_donors_hotspots():
    """API endpoint for proximity-filtered donor clusters with coordinate masking (AC 2)."""
    radius = int(request.args.get("radius", 50))
    blood_type = request.args.get("blood_type", "All")

    filtered = [h for h in raw_hotspots if h["distance"] <= radius]
    if blood_type != "All":
        filtered = [h for h in filtered if h["blood_type"] == blood_type]

    sanitized = []
    for h in filtered:
        sanitized.append({
            "district": h["district"],
            "count": h["count"],
            "blood_type": h["blood_type"],
            "distance": h["distance"],
            "privacy_masked_coords": {
                "latitude_coarse": h["latitude_coarse"],
                "longitude_coarse": h["longitude_coarse"]
            }
        })

    return jsonify({
        "radius_km": radius,
        "blood_type_filter": blood_type,
        "hotspots": sanitized
    }), 200


@app.route("/api/v1/districts", methods=["GET"])
def api_districts():
    """API endpoint for fallback district list view (REQ-F-011)."""
    return jsonify({"districts": districts_registry}), 200


@app.route("/api/v1/requests", methods=["GET", "POST"])
def api_requests():
    """API endpoint to create requests (AC 3) or list active requests for donors (AC 4)."""
    if request.method == "POST":
        blood_type = request.form.get("blood_type") or request.json.get("blood_type") if request.is_json else None
        units = request.form.get("units") or (request.json.get("units") if request.is_json else 1)
        urgency = request.form.get("urgency", "Critical")
        district = request.form.get("district", "Downtown")
        notes = request.form.get("notes", "")

        if not blood_type:
            return jsonify({"error": "blood_type is required"}), 400

        new_id = len(demands) + 1
        new_demand = {
            "id": new_id,
            "hospital": "API Recipient",
            "blood_type": blood_type,
            "units": int(units),
            "filename": "prescription_upload.pdf",
            "status": "Pending",
            "urgency": urgency,
            "district": district,
            "notes": notes,
            "created_at": datetime.now().isoformat()
        }
        demands.append(new_demand)

        return jsonify({
            "status": 201,
            "schema": {
                "id": new_id,
                "recipient": "API Recipient",
                "blood_type": blood_type,
                "units": int(units),
                "urgency": urgency,
                "filename": "prescription_upload.pdf",
                "status": "Pending",
                "created_at": new_demand["created_at"]
            }
        }), 201

    # GET active requests (AC 4)
    status_filter = request.args.get("status", "All")
    res = demands if status_filter == "All" else [d for d in demands if d.get("status") == status_filter]
    return jsonify({"requests": res}), 200


@app.route("/api/v1/donor/gamification", methods=["GET"])
def api_donor_gamification():
    """API endpoint for gamification metrics (REQ-F-002)."""
    return jsonify({
        "total_points": 1250,
        "lives_impacted": 5,
        "donations_count": 5,
        "badges": _get_donor_badges(5)
    }), 200


@app.route("/api/v1/donor/share-badge", methods=["POST"])
def api_share_badge():
    """API endpoint for social sharing (REQ-F-007)."""
    data = request.get_json(silent=True) or {}
    badge_name = data.get("badge_name", "Achievement")
    platform = data.get("platform", "twitter")

    return jsonify({
        "success": True,
        "message": f"Successfully shared badge '{badge_name}' to {platform}.",
        "badge": badge_name,
        "shared_at": datetime.now().isoformat()
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
