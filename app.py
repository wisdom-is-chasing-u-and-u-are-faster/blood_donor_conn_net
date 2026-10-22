# This is a Flask web application for a Blood Donor Connection Network.
# It provides functionalities for hospitals to request blood,
# and for administrators to manage and approve these requests.
# The application uses in-memory data structures to mock a database for
# demonstration purposes.
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify, send_from_directory

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

# Verification documents for District Administrator review workflow (REQ-F-009, REQ-F-010)
verification_documents = [
    {
        "id": "doc-101",
        "user_id": "user-id-12345",
        "user_email": "user_a@email.com",
        "document_type": "Donor ID Card",
        "filename": "donor_id_card_scan.pdf",
        "status": "Pending",
        "district": "Downtown",
        "uploaded_at": "2023-10-26 10:30 AM",
        "consent": True,
        "encrypted_uri": "gs://bdcn-encrypted-docs-vault/documents/doc-101.enc"
    },
    {
        "id": "doc-102",
        "user_id": "user-id-67890",
        "user_email": "user_b@email.com",
        "document_type": "Medical Clearance Form",
        "filename": "clearance_med.pdf",
        "status": "Pending",
        "district": "North District",
        "uploaded_at": "2023-10-26 09:15 AM",
        "consent": True,
        "encrypted_uri": "gs://bdcn-encrypted-docs-vault/documents/doc-102.enc"
    },
    {
        "id": "doc-103",
        "user_id": "user-id-abcde",
        "user_email": "user_c@email.com",
        "document_type": "Other Identification",
        "filename": "govt_id_verification.pdf",
        "status": "Pending",
        "district": "East Valley",
        "uploaded_at": "2023-10-27 09:00 AM",
        "consent": True,
        "encrypted_uri": "gs://bdcn-encrypted-docs-vault/documents/doc-103.enc"
    }
]

notifications = [
    {
        "id": "notif-001",
        "title": "Welcome to BDCN",
        "message": "Thank you for registering. Upload your donor verification document to get started.",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read": False
    }
]

try:
    from db.init_db import init_database
    init_database()
except Exception:
    pass


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
        if username and password:  # Allow simple password matching for mock flow
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

        # Verify from mock donor database
        target_donor = next(
            (d for d in donors if d["username"] == username), None)
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
    # Mock social media authentication
    username = f"social_{provider}_user"
    name = f"Social {provider.capitalize()} User"

    # Auto register/get social donor
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
        f"Successfully authenticated via {
            provider.capitalize()}!",
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

        # Check duplicate
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

    # Generate badges based on donation count
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

    # Mock personal donation history
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

    # Filter density clusters by radius and blood type
    filtered = [h for h in raw_hotspots if h["distance"] <= radius]
    if blood_type != "All":
        filtered = [h for h in filtered if h["blood_type"] == blood_type]

    return render_template(
        "map_hotspots.html", hotspots=filtered, radius=radius, blood_type=blood_type)


# --- ARCH-5065 Routes & Static Serving ---

@app.route("/health")
def health():
    """Service health and readiness probe for Cloud Run container orchestration."""
    return jsonify({
        "status": "ok",
        "service": "blood_donor_conn_net",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/login")
@app.route("/login.html")
def serve_login():
    return send_from_directory("public", "login.html")


@app.route("/dashboard")
@app.route("/dashboard.html")
def serve_dashboard():
    return send_from_directory("public", "dashboard.html")


@app.route("/upload")
@app.route("/upload.html", methods=["GET", "POST"])
def serve_upload():
    if request.method == "POST":
        return api_upload_document()
    return send_from_directory("public", "upload.html")


@app.route("/admin/dashboard")
@app.route("/admin_dashboard.html")
def serve_admin_dashboard():
    return send_from_directory("public", "admin_dashboard.html")


@app.route("/admin/review")
@app.route("/admin_review.html")
def serve_admin_review():
    return send_from_directory("public", "admin_review.html")


@app.route("/index.html")
def serve_index():
    return send_from_directory("public", "index.html")


@app.route("/pages/<path:filename>")
def serve_pages(filename):
    return send_from_directory("public/pages", filename)


# --- ARCH-5065 REST API Endpoints ---

@app.route("/api/v1/auth/social", methods=["POST"])
def api_social_login():
    """Authenticate user via social OAuth providers: Google, Apple, or Facebook (REQ-F-008)."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    provider = (data.get("provider") or "google").lower()
    if "google" in provider:
        provider = "google"
    elif "apple" in provider:
        provider = "apple"
    elif "facebook" in provider:
        provider = "facebook"
    else:
        return jsonify({"status": "error", "message": f"Unsupported provider: {provider}"}), 400

    username = f"social_{provider}_user"
    name = f"Social {provider.capitalize()} User"
    email = data.get("email", f"{username}@bdcn.org")

    target_donor = next((d for d in donors if d["username"] == username), None)
    if not target_donor:
        target_donor = {
            "name": name,
            "username": username,
            "email": email,
            "age": 26,
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
        "details": f"User '{username}' authenticated via OAuth 2.0 {provider.capitalize()}-",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "status": "authenticated",
        "user": {
            "id": username,
            "name": name,
            "email": email,
            "provider": provider,
            "role": "donor"
        },
        "token": f"mock-oauth2-jwt-token-{provider}-session"
    }), 200


@app.route("/api/v1/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "donor")

    if not username or not password:
        return jsonify({"status": "error", "message": "Missing credentials"}), 400

    session["username"] = username
    session["role"] = role
    audit_logs.append({
        "action": "API LOGIN",
        "details": f"User '{username}' logged in with role '{role}'.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return jsonify({"status": "success", "role": role, "username": username}), 200


@app.route("/api/v1/auth/logout", methods=["POST"])
def api_logout():
    user = session.get("username", "anonymous")
    session.clear()
    audit_logs.append({
        "action": "API LOGOUT",
        "details": f"User '{user}' logged out.",
        "user": user,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return jsonify({"status": "logged_out"}), 200


@app.route("/api/v1/donors/hotspots", methods=["GET"])
def api_donor_hotspots():
    """Retrieve coarse centroid clusters for Google Maps SDK display (REQ-F-005, REQ-F-006)."""
    radius = int(request.args.get("radius", 50))
    blood_type = request.args.get("blood_type", "All")

    clusters = []
    for h in raw_hotspots:
        if h["distance"] <= radius:
            if blood_type == "All" or h["blood_type"] == blood_type:
                # Convert raw hotspot into coarse centroid cluster representation
                clusters.append({
                    "district": h["district"],
                    "coarse_latitude": round(37.75 + (h.get("top", 50) - 50) * 0.005, 2),
                    "coarse_longitude": round(-122.42 + (h.get("left", 50) - 50) * 0.005, 2),
                    "donor_count": h["count"],
                    "primary_blood_types": [h["blood_type"]],
                    "distance_km": h["distance"],
                    "urgency_level": "High" if h["count"] > 15 else "Normal"
                })

    return jsonify({
        "total_clusters": len(clusters),
        "clusters": clusters
    }), 200


@app.route("/api/v1/documents/upload", methods=["POST"])
def api_upload_document():
    """Upload verification document into encrypted repository
    with audit trailing (REQ-F-003, REQ-F-004, REQ-N-001, REQ-N-003)."""
    file = request.files.get("document") or request.files.get("file")
    doc_type = request.form.get("document_type", "Donor ID Card")
    consent = request.form.get("consent", "true").lower() in ["true", "1", "yes", "on"]
    user_email = request.form.get("user_email", session.get("username", "donor_anonymous@bdcn.org"))

    filename = file.filename if file else f"upload_{int(datetime.now().timestamp())}.pdf"
    doc_id = f"doc-{len(verification_documents) + 101}"
    bucket = os.environ.get("GCP_STORAGE_BUCKET", "bdcn-encrypted-docs-vault")
    encrypted_uri = f"gs://{bucket}/documents/{doc_id}.enc"

    new_doc = {
        "id": doc_id,
        "user_id": session.get("username", "donor_user"),
        "user_email": user_email,
        "document_type": doc_type,
        "filename": filename,
        "status": "Pending",
        "district": "Downtown",
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "consent": consent,
        "encrypted_uri": encrypted_uri
    }
    verification_documents.append(new_doc)

    audit_logs.append({
        "action": "DOCUMENT UPLOAD",
        "details": (
            f"Document #{doc_id} ({doc_type}) uploaded by {user_email}. "
            f"Encrypted at rest in {encrypted_uri} (30-day lifecycle)."
        ),
        "user": user_email,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    notifications.append({
        "id": f"notif-{len(notifications) + 1}",
        "title": "Document Received",
        "message": f"Your {doc_type} ({filename}) was uploaded and is pending district administrator review.",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read": False
    })

    if request.is_json or request.path.startswith("/api/"):
        return jsonify({
            "status": "Pending",
            "document_id": doc_id,
            "retention_days": 30,
            "encrypted_uri": encrypted_uri,
            "audit_id": str(len(audit_logs))
        }), 201
    else:
        flash("Document submitted successfully for verification!", "success")
        return redirect(url_for("serve_dashboard"))


@app.route("/api/v1/admin/verifications", methods=["GET"])
def api_list_verifications():
    """List pending document verifications for district administrator (REQ-F-009, REQ-F-010)."""
    pending = [d for d in verification_documents if d["status"] == "Pending"]
    return jsonify({
        "total_pending": len(pending),
        "items": pending
    }), 200


@app.route("/api/v1/admin/verifications/<doc_id>", methods=["GET"])
def api_get_verification(doc_id):
    target = next((d for d in verification_documents if d["id"] == doc_id), None)
    if not target:
        return jsonify({"status": "error", "message": "Verification case not found"}), 404
    return jsonify(target), 200


@app.route("/api/v1/admin/verifications/<doc_id>/action", methods=["POST"])
def api_review_verification(doc_id):
    """Administrator review decision: Approve or Reject verification document (REQ-F-009)."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    action = data.get("action", "").lower()
    if action not in ["approve", "reject"]:
        return jsonify({"status": "error", "message": "Invalid action. Must be 'approve' or 'reject'"}), 400

    target = next((d for d in verification_documents if d["id"] == doc_id), None)
    if not target:
        return jsonify({"status": "error", "message": "Verification case not found"}), 404

    target["status"] = "Approved" if action == "approve" else "Rejected"
    target["reviewed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reviewer = session.get("username", "admin_district")
    target["reviewed_by"] = reviewer

    audit_logs.append({
        "action": f"DOCUMENT VERIFICATION {action.upper()}ED",
        "details": f"Administrator '{reviewer}' {action}ed verification document #{doc_id} for {target['user_email']}.",
        "user": reviewer,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    notifications.append({
        "id": f"notif-{len(notifications) + 1}",
        "title": f"Verification Document {action.capitalize()}ed",
        "message": (
            f"Your verification document #{doc_id} ({target['document_type']}) "
            f"has been {action}ed by your district administrator."
        ),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read": False
    })

    return jsonify({
        "id": doc_id,
        "status": target["status"],
        "verified_by": reviewer,
        "verified_at": target["reviewed_at"]
    }), 200


@app.route("/api/v1/audit/logs", methods=["GET"])
def api_audit_logs():
    """Retrieve audit trails for document uploads and admin reviews (REQ-F-004)."""
    return jsonify({"logs": audit_logs}), 200


@app.route("/api/v1/notifications", methods=["GET"])
def api_notifications():
    """Retrieve user notifications (REQ-F-007, REQ-N-002)."""
    return jsonify({"notifications": notifications}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
