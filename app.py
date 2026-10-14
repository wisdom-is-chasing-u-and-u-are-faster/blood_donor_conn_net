# This is a Flask web application for a Blood Donor Connection Network.
# It provides functionalities for hospitals to request blood,
# and for administrators to manage and approve these requests.
# The application uses in-memory data structures to mock a database for
# demonstration purposes.
import os
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, session,
    flash, url_for, jsonify, send_from_directory
)

app = Flask(__name__, static_folder="public", static_url_path="")
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

# Structured donor clusters for coarse centroid clustering (REQ-F-008, REQ-F-009)
donor_clusters = [
    {
        "cluster_id": "cluster_dt_01",
        "district": "Downtown District",
        "centroid_lat": 37.77,
        "centroid_lng": -122.42,
        "donor_count": 18,
        "blood_types": ["O-", "O+", "A+"],
        "density_tier": "High"
    },
    {
        "cluster_id": "cluster_nd_02",
        "district": "North District",
        "centroid_lat": 37.79,
        "centroid_lng": -122.40,
        "donor_count": 12,
        "blood_types": ["A+", "B+"],
        "density_tier": "Medium"
    },
    {
        "cluster_id": "cluster_ed_03",
        "district": "East Bay Cluster",
        "centroid_lat": 37.80,
        "centroid_lng": -122.27,
        "donor_count": 24,
        "blood_types": ["O+", "A-", "AB+"],
        "density_tier": "High"
    },
    {
        "cluster_id": "cluster_sd_04",
        "district": "South Bay Area",
        "centroid_lat": 37.33,
        "centroid_lng": -121.89,
        "donor_count": 9,
        "blood_types": ["B-", "O+"],
        "density_tier": "Low"
    }
]

# Medical document repository records (REQ-F-003, REQ-N-001)
medical_documents = [
    {
        "id": 1,
        "filename": "donor_eligibility_attestation.pdf",
        "document_type": "Eligibility Form",
        "verification_status": "Verified",
        "uploaded_at": "2026-10-10 14:00:00",
        "notes": "Pre-screened health questionnaire approved."
    },
    {
        "id": 2,
        "filename": "serology_clearance.pdf",
        "document_type": "Lab Serology Test",
        "verification_status": "Verified",
        "uploaded_at": "2026-10-12 09:30:00",
        "notes": "Non-reactive panels on all infectious markers."
    }
]

# Gamification achievements and badge tiers (REQ-F-002)
achievements_list = [
    {
        "id": "first_drop",
        "code": "FIRST_DROP",
        "title": "First Drop",
        "description": "Completed your initial whole blood donation.",
        "badge_icon": "🩸",
        "tier": "Bronze",
        "points_reward": 50,
        "unlocked": True
    },
    {
        "id": "lifesaver",
        "code": "LIFESAVER",
        "title": "Lifesaver",
        "description": "Donated 3 or more times to emergency alerts.",
        "badge_icon": "⭐",
        "tier": "Silver",
        "points_reward": 150,
        "unlocked": True
    },
    {
        "id": "champion",
        "code": "CHAMPION",
        "title": "Community Champion",
        "description": "Achieved 5 donations and inspired 3 peers.",
        "badge_icon": "🏆",
        "tier": "Gold",
        "points_reward": 300,
        "unlocked": True
    },
    {
        "id": "century_club",
        "code": "CENTURY_CLUB",
        "title": "Century Club",
        "description": "Over 10 units donated across community drives.",
        "badge_icon": "👑",
        "tier": "Platinum",
        "points_reward": 500,
        "unlocked": False
    }
]


# ---------------------------------------------------------
# Static Serving & Health Check (Cloud Run)
# ---------------------------------------------------------
@app.route("/js/<path:filename>")
def serve_js(filename):
    """Serve client-side JavaScript files from public/js."""
    return send_from_directory(os.path.join(app.root_path, "public", "js"), filename)


@app.route("/health")
def health_check():
    """Health and readiness probe for Cloud Run container orchestrator."""
    return jsonify({
        "status": "ok",
        "service": "bdcn-platform",
        "version": "1.0.0"
    }), 200


# ---------------------------------------------------------
# Variant-A UI Screen Routes (ARCH-3619)
# ---------------------------------------------------------
@app.route("/index")
@app.route("/preview")
def full_preview_hub():
    """AC 5: Full UI Prototype Screen Hub connecting all self-contained screens."""
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login_view():
    """AC 1: Variant-A Login with Social Media buttons."""
    if request.method == "POST":
        provider = request.form.get("provider", "google")
        return redirect(url_for("social_login", provider=provider))
    return render_template("login.html")


@app.route("/dashboard")
def dashboard_view():
    """Variant-A Dashboard & Request Feed."""
    formatted_requests = [
        {
            "id": d["id"],
            "recipient_name": d.get("hospital", "General Hospital"),
            "hospital": d.get("hospital", "General Hospital"),
            "blood_type": d["blood_type"],
            "units": d["units"],
            "urgency": d.get("urgency", "Standard"),
            "status": d.get("status", "Pending Donor Match"),
            "district": d.get("district", "Downtown")
        }
        for d in demands
    ]
    return render_template("dashboard.html", requests=formatted_requests)


@app.route("/map")
def map_view():
    """AC 2: Main map view displaying clustered data points, not individual addresses."""
    return render_template("map.html", clusters=donor_clusters)


@app.route("/profile")
def profile_view():
    """AC 3: Access profile section with interface to upload a document."""
    username = session.get("username", "johndoe")
    target_donor = next((d for d in donors if d["username"] == username), None)
    if not target_donor:
        user_info = {
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "blood_type": "O+",
            "district": "Downtown",
            "total_donations": 5
        }
    else:
        user_info = {
            "full_name": target_donor.get("name", "John Doe"),
            "email": f"{username}@example.com",
            "blood_type": target_donor.get("blood_group", "O+"),
            "district": target_donor.get("district", "Downtown"),
            "total_donations": target_donor.get("donation_count", 5)
        }
    return render_template("profile.html", user=user_info, documents=medical_documents)


@app.route("/profile/upload", methods=["POST"])
def profile_document_upload():
    """AC 3: Handle medical document upload with audit trail."""
    file = request.files.get("file")
    notes = request.form.get("notes", "")
    if not file or not file.filename:
        flash("Please select a valid medical document to upload.", "danger")
        return redirect(url_for("profile_view"))

    new_doc_id = len(medical_documents) + 1
    new_doc = {
        "id": new_doc_id,
        "filename": file.filename,
        "document_type": request.form.get("document_type", "Medical Clearance"),
        "verification_status": "Pending Review",
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "notes": notes
    }
    medical_documents.append(new_doc)
    audit_logs.append({
        "action": "DOCUMENT_UPLOAD",
        "details": f"Medical document '{file.filename}' uploaded to secure GCP repository. Notes: {notes}",
        "user": session.get("username", "DonorUser"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    flash(f"Document '{file.filename}' uploaded successfully for clinical review.", "success")
    return redirect(url_for("profile_view"))


@app.route("/achievements")
def achievements_view():
    """AC 4: Functional achievements/gamification screen."""
    return render_template(
        "achievements.html",
        tier="Silver",
        points=250,
        achievements=achievements_list
    )


@app.route("/settings", methods=["GET", "POST"])
def settings_view():
    """Variant-A Settings screen."""
    if request.method == "POST":
        flash("Settings saved successfully.", "success")
    return render_template("settings.html")


# ---------------------------------------------------------
# REST API Endpoints (Matching api_contract.json)
# ---------------------------------------------------------
@app.route("/api/v1/auth/social-login", methods=["POST"])
def api_social_login():
    """AC 1: Social Media login via REST API."""
    data = request.get_json(silent=True) or {}
    provider = data.get("provider", "google").lower()
    email = data.get("email", f"user@{provider}.com")
    name = data.get("name", f"Social {provider.capitalize()} User")

    username = f"social_{provider}_user"
    session["username"] = username
    session["role"] = "donor"

    audit_logs.append({
        "action": "API_SOCIAL_LOGIN",
        "details": f"Social login authenticated via {provider.capitalize()} for {email}.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "status": "success",
        "user_id": username,
        "role": "donor",
        "name": name,
        "email": email,
        "token": f"jwt-mock-token-{provider}"
    }), 200


@app.route("/api/v1/map/clusters", methods=["GET"])
def api_map_clusters():
    """AC 2: Return coarse centroid clusters without individual addresses."""
    return jsonify({
        "status": "success",
        "clusters": donor_clusters,
        "privacy_guarantee": "HIPAA-compliant coarse centroid clustering; zero raw addresses exposed."
    }), 200


@app.route("/api/v1/profile", methods=["GET", "POST"])
def api_profile():
    """AC 3: Profile and documents metadata."""
    if request.method == "POST":
        return jsonify({"status": "success", "updated": True}), 200
    return jsonify({
        "status": "success",
        "user_id": session.get("username", "johndoe"),
        "name": "John Doe",
        "blood_type": "O+",
        "district": "Downtown",
        "total_donations": 5,
        "documents": medical_documents
    }), 200


@app.route("/api/v1/documents/upload", methods=["POST"])
def api_upload_document():
    """AC 3: Medical document upload with audit trail."""
    file = request.files.get("file")
    filename = file.filename if file else request.form.get("filename", "medical_clearance.pdf")
    doc_type = request.form.get("document_type", "Medical Clearance")
    notes = request.form.get("notes", "")

    new_id = len(medical_documents) + 1
    new_doc = {
        "id": new_id,
        "filename": filename,
        "document_type": doc_type,
        "verification_status": "Pending Review",
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "notes": notes
    }
    medical_documents.append(new_doc)
    audit_logs.append({
        "action": "API_DOCUMENT_UPLOAD",
        "details": f"API uploaded medical document '{filename}' ({doc_type}).",
        "user": session.get("username", "DonorUser"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return jsonify({
        "status": "success",
        "doc_id": str(new_id),
        "filename": filename,
        "verification_status": "Pending Review",
        "audit_event_id": f"evt-{new_id}"
    }), 201


@app.route("/api/v1/documents", methods=["GET"])
def api_get_documents():
    return jsonify({
        "status": "success",
        "documents": medical_documents
    }), 200


@app.route("/api/v1/achievements", methods=["GET"])
def api_get_achievements():
    """AC 4: Return achievements, tiers, and points."""
    return jsonify({
        "status": "success",
        "points": 250,
        "current_tier": "Silver",
        "achievements": achievements_list
    }), 200


@app.route("/api/v1/achievements/share", methods=["POST"])
def api_share_achievement():
    """AC 4: Achievement social sharing endpoint."""
    data = request.get_json(silent=True) or {}
    ach_id = data.get("achievement_id", "first_drop")
    platform = data.get("platform", "twitter")

    audit_logs.append({
        "action": "ACHIEVEMENT_SHARED",
        "details": f"Achievement '{ach_id}' shared on platform '{platform}'.",
        "user": session.get("username", "DonorUser"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return jsonify({
        "status": "success",
        "share_url": f"https://bdcn.health/achievements/{ach_id}",
        "share_text": f"Proud to support BDCN! Unlocked milestone #{ach_id}."
    }), 200


@app.route("/api/v1/dashboard/requests", methods=["GET"])
def api_dashboard_requests():
    return jsonify({
        "status": "success",
        "requests": demands
    }), 200


@app.route("/api/v1/settings", methods=["GET", "POST"])
def api_settings():
    return jsonify({
        "status": "success",
        "updated": True,
        "settings": {
            "push_notifications": True,
            "sms_fallback": True,
            "privacy_obfuscation": True
        }
    }), 200


@app.route("/api/v1/audit/logs", methods=["GET"])
def api_audit_logs():
    return jsonify({
        "status": "success",
        "logs": audit_logs
    }), 200


# ---------------------------------------------------------
# Existing Legacy Endpoints (Maintained for full backward compat)
# ---------------------------------------------------------
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
            flash(f"Welcome, {username}!", "success")
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
                "details": f"Donor user '{username}' logged in.",
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
    flash(
        f"Successfully authenticated via {provider.capitalize()}!",
        "success")
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
    flash(
        f"Successfully shared your {clean_badge} badge to your social profiles!",
        "success")
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
            flash(
                "All fields including compliance document upload are required.",
                "danger")
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
            "details": (
                f"Demand #{new_id} ({blood_type}, {units} units) created for {district} "
                f"with urgency {urgency}. File: {filename}. Notes: {notes}"
            ),
            "user": session.get("username"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        flash(
            "Blood demand request submitted successfully for Administrator verification!",
            "success")
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
        pending_demands = [d for d in pending_demands if d.get(
            "district") == filter_district]

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
                "details": (
                    f"Approved demand #{demand_id} ({target_demand['blood_type']}) "
                    f"for {target_demand.get('district', 'Downtown')}. Emitted event."
                ),
                "user": session.get("username"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash(
                f"Approved demand #{demand_id}! Alert dispatched to nearby donors.",
                "success")
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
