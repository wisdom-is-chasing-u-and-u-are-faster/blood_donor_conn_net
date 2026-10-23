# This is a Flask web application for a Blood Donor Connection Network.
# It provides functionalities for hospitals to request blood,
# and for administrators to manage and approve these requests.
# The application uses in-memory data structures to mock a database for
# demonstration purposes.
import os
import hashlib
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "super-secret-bdcn-key-12345")

# H3 Hexagonal Discretization & Obfuscation Helper
def lat_lng_to_h3_cluster(lat, lng, resolution=7):
    """
    Simulates Uber H3 hexagonal spatial discretization (Resolution 7 / ~1.2km radius).
    Ensures raw coordinates are NEVER stored or returned; only the H3 cell index is retained.
    """
    coord_str = f"{round(float(lat), 2)}:{round(float(lng), 2)}:{resolution}"
    digest = hashlib.sha256(coord_str.encode()).hexdigest()[:15]
    return f"8728{digest}ffffff"

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
        "donation_count": 5,
        "last_whole_blood": "2025-11-15",
        "last_platelets": None,
        "h3_cluster": "872830828ffffff"
    },
    {
        "name": "John Doe",
        "username": "johndoe",
        "age": 34,
        "gender": "Male",
        "blood_group": "A+",
        "last_donation": "2025-08-20",
        "donation_count": 2,
        "last_whole_blood": "2025-08-20",
        "last_platelets": None,
        "h3_cluster": "87283082bffffff"
    }
]

# Recipient Blood Requests (ARCH-5400)
recipient_requests = [
    {
        "id": 1,
        "case_id": "REQ-781A",
        "recipient_name": "City General Hospital",
        "blood_type": "A+",
        "donation_type": "Whole Blood",
        "urgency": "Urgent",
        "submitted": "10:45 AM",
        "time_in_queue": "8 mins",
        "h3_cluster": "872830828ffffff",
        "document_name": "medical_req_781.pdf",
        "notes": "Scheduled surgery on Friday.",
        "status": "Pending"
    },
    {
        "id": 2,
        "case_id": "REQ-780B",
        "recipient_name": "Community Blood Center",
        "blood_type": "O-",
        "donation_type": "Platelets",
        "urgency": "Standard",
        "submitted": "10:42 AM",
        "time_in_queue": "11 mins",
        "h3_cluster": "87283082bffffff",
        "document_name": "requisition_780b.png",
        "notes": "Emergency platelet reserves required.",
        "status": "Pending"
    },
    {
        "id": 3,
        "case_id": "REQ-779C",
        "recipient_name": "Metro Clinic",
        "blood_type": "B+",
        "donation_type": "Whole Blood",
        "urgency": "Standard",
        "submitted": "10:31 AM",
        "time_in_queue": "22 mins",
        "h3_cluster": "872830828ffffff",
        "document_name": "doc_779c.pdf",
        "notes": "Post-op recovery replenishment.",
        "status": "Approved"
    }
]

notifications_store = [
    {
        "id": 1,
        "title": "Urgent Need: A+ Blood",
        "message": "A patient at City General Hospital requires immediate A+ blood donation for a scheduled surgery.",
        "h3_cluster": "872830828ffffff",
        "blood_type": "A+",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login_hospital.html")


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
            flash(f"Welcome back, District Administrator {username}!", "success")
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
            session["username"] = username
            session["role"] = "donor"
            audit_logs.append({
                "action": "DONOR LOGIN",
                "details": f"Donor '{username}' logged in successfully.",
                "user": username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash(f"Welcome, {donor['name']}!", "success")
            return redirect(url_for("donor_profile"))
        else:
            flash("Invalid donor credentials.", "danger")
    return render_template("login_donor.html")


@app.route("/login/social/<provider>")
def social_login(provider):
    if provider not in ["google", "apple", "facebook"]:
        flash("Unsupported social provider.", "danger")
        return redirect(url_for("login_donor"))

    username = f"social_{provider}_user"
    if not any(d["username"] == username for d in donors):
        donors.append({
            "name": f"{provider.capitalize()} User",
            "username": username,
            "age": 30,
            "gender": "Other",
            "blood_group": "O+",
            "last_donation": "2025-06-01",
            "donation_count": 3,
            "last_whole_blood": "2025-06-01",
            "last_platelets": None,
            "h3_cluster": "872830828ffffff"
        })

    session["username"] = username
    session["role"] = "donor"

    audit_logs.append({
        "action": "SOCIAL LOGIN",
        "details": f"User logged in via {provider.capitalize()}.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    provider_name = provider.capitalize()
    flash(f"Successfully authenticated via {provider_name}!", "success")
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
            "last_whole_blood": last_donation,
            "last_platelets": None,
            "h3_cluster": "872830828ffffff"
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
        flash("Unauthorized. Please log in as a donor.", "danger")
        return redirect(url_for("login_donor"))

    current_user = session.get("username")
    donor_info = next(
        (d for d in donors if d["username"] == current_user),
        None)
    if not donor_info:
        donor_info = {
            "name": "Jane Smith",
            "username": "janesmith",
            "age": 28,
            "gender": "Female",
            "blood_group": "O-",
            "last_donation": "2025-11-15",
            "donation_count": 5
        }

    count = donor_info.get("donation_count", 0)
    badges = []
    if count >= 1:
        badges.append({
            "name": "First Drop",
            "desc": "Completed first blood donation",
            "description": "Completed first blood donation",
            "icon": "bi-droplet-fill",
            "status": "Earned",
            "earned": True
        })
    else:
        badges.append({
            "name": "First Drop",
            "desc": "Complete 1 donation",
            "description": "Complete 1 donation",
            "icon": "bi-droplet",
            "status": "Locked",
            "earned": False
        })

    if count >= 3:
        badges.append({
            "name": "Silver Lifesaver",
            "desc": "Completed 3 donations",
            "description": "Completed 3 donations",
            "icon": "bi-shield-shaded",
            "status": "Earned",
            "earned": True
        })
    else:
        badges.append({
            "name": "Silver Lifesaver",
            "desc": "Complete 3 donations",
            "description": "Complete 3 donations",
            "icon": "bi-shield",
            "status": "Locked",
            "earned": False
        })

    if count >= 5:
        badges.append({
            "name": "Gold Guardian",
            "desc": "Completed 5+ donations",
            "description": "Completed 5+ donations",
            "icon": "bi-trophy-fill",
            "status": "Earned",
            "earned": True
        })
    else:
        badges.append({
            "name": "Gold Guardian",
            "desc": "Complete 5 donations",
            "description": "Complete 5 donations",
            "icon": "bi-trophy",
            "status": "Locked",
            "earned": False
        })

    return render_template(
        "donor_profile.html", donor=donor_info, badges=badges)


@app.route("/donor/share/<badge_name>", methods=["POST"])
def share_badge(badge_name):
    if session.get("role") != "donor":
        flash("Unauthorized. Please log in.", "danger")
        return redirect(url_for("login_donor"))

    user = session.get("username")
    clean_badge = badge_name.replace("-", " ")

    audit_logs.append({
        "action": "BADGE SHARED",
        "details": f"Donor '{user}' shared achievement badge '{clean_badge}' on social media.",
        "user": user,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    flash(
        f"Successfully shared your {clean_badge} badge to your social network!",
        "success")
    return redirect(url_for("donor_profile"))


@app.route("/hospital/dashboard")
def hospital_dashboard():
    if session.get("role") != "hospital":
        flash("Unauthorized. Please log in as hospital staff.", "danger")
        return redirect(url_for("login_hospital"))
    return render_template(
        "dashboard.html",
        demands=demands,
        scheduled_donors=scheduled_donors)


@app.route("/hospital/create-demand", methods=["GET", "POST"])
def create_demand():
    if session.get("role") != "hospital":
        flash("Unauthorized. Please log in as hospital staff.", "danger")
        return redirect(url_for("login_hospital"))

    if request.method == "POST":
        blood_type = request.form.get("blood_type")
        units = request.form.get("units")
        notes = request.form.get("notes")
        urgency = request.form.get("urgency", "Routine")
        district = request.form.get("district", "Downtown")
        document = request.files.get("document")

        if not blood_type or not units or not district:
            flash("All required fields must be filled.", "danger")
            return redirect(url_for("create_demand"))

        filename = document.filename if document and document.filename else "medical_requisition.pdf"

        demand_id = len(demands) + 1
        new_demand = {
            "id": demand_id,
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
            "action": "HOSPITAL DEMAND CREATED",
            "details": f"Demand #{demand_id} ({blood_type}, {units} units, {urgency}) created by {session.get('username')}.",
            "user": session.get("username"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        flash(
            f"Blood demand request submitted successfully! Tracking ID: #{demand_id}",
            "success")
        return redirect(url_for("hospital_dashboard"))

    return render_template("create_demand.html")


@app.route("/admin/queue")
def admin_queue():
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in as administrator.", "danger")
        return redirect(url_for("login_admin"))
    return render_template("verification_queue.html", demands=demands)


@app.route("/admin/verify/<int:demand_id>", methods=["POST"])
def verify_demand(demand_id):
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in as administrator.", "danger")
        return redirect(url_for("login_admin"))

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
                "details": f"Approved demand #{demand_id} ({target_demand['blood_type']}). Emitted alert to nearby donor cluster.",
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


# ==============================================================================
# ARCH-5400 Endpoints & Variant-A UI Routes
# ==============================================================================

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "bdcn-service"}), 200


@app.route("/pages/<page_name>")
def serve_variant_page(page_name):
    """Serves high-fidelity Variant-A pages matching visual mockups."""
    template_name = page_name if page_name.endswith(".html") else f"{page_name}.html"
    snake_name = template_name.replace("-", "_")
    return render_template(snake_name)


@app.route("/api/v1/auth/social", methods=["POST"])
def api_social_login():
    data = request.get_json() or {}
    provider = data.get("provider", "google").lower()
    email = data.get("email", f"user@{provider}.com")
    name = data.get("name", f"{provider.capitalize()} User")
    lat = data.get("lat")
    lng = data.get("lng")
    
    # H3 Geolocation Discretization - Raw lat/lng are converted and discarded
    if lat is not None and lng is not None:
        h3_cluster = lat_lng_to_h3_cluster(lat, lng)
    else:
        h3_cluster = data.get("h3_index", "872830828ffffff")

    username = f"social_{provider}_{email.split('@')[0]}"
    donor = next((d for d in donors if d["username"] == username), None)
    if not donor:
        donor = {
            "name": name,
            "username": username,
            "age": 29,
            "gender": "Other",
            "blood_group": "O+",
            "last_donation": None,
            "donation_count": 0,
            "last_whole_blood": None,
            "last_platelets": None,
            "h3_cluster": h3_cluster
        }
        donors.append(donor)

    session["username"] = username
    session["role"] = "donor"

    audit_logs.append({
        "action": "OAUTH2 SOCIAL LOGIN",
        "details": f"User authenticated via {provider.capitalize()} with H3 spatial cluster {h3_cluster}.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "status": "success",
        "user_id": username,
        "username": username,
        "role": "donor",
        "token": f"jwt-mock-token-{provider}-auth",
        "h3_cluster": h3_cluster
    }), 200


@app.route("/api/v1/requests", methods=["GET", "POST"])
def api_recipient_requests():
    if request.method == "POST":
        data = request.get_json() or request.form.to_dict()
        blood_type = data.get("blood_type", "A+")
        donation_type = data.get("donation_type", "Whole Blood")
        urgency = data.get("urgency", "Urgent")
        notes = data.get("notes", "")
        document_name = data.get("document_name")
        lat = data.get("lat")
        lng = data.get("lng")

        # Discretize raw location into H3 spatial hexagon
        if lat is not None and lng is not None:
            h3_cluster = lat_lng_to_h3_cluster(lat, lng)
        else:
            h3_cluster = data.get("h3_index", "872830828ffffff")

        # Check for uploaded document in multipart form
        if "document" in request.files:
            file = request.files["document"]
            if file and file.filename:
                document_name = file.filename

        if not document_name:
            document_name = "requisition_document.pdf"

        req_id = len(recipient_requests) + 1
        case_id = f"REQ-78{req_id}D"

        new_req = {
            "id": req_id,
            "case_id": case_id,
            "recipient_name": session.get("username", "Alex Doe"),
            "blood_type": blood_type,
            "donation_type": donation_type,
            "urgency": urgency,
            "submitted": datetime.now().strftime("%I:%M %p"),
            "time_in_queue": "1 min",
            "h3_cluster": h3_cluster,
            "document_name": document_name,
            "notes": notes,
            "status": "Pending"
        }
        recipient_requests.append(new_req)

        audit_logs.append({
            "action": "RECIPIENT REQUEST SUBMITTED",
            "details": f"New blood request {case_id} ({blood_type}, {donation_type}) submitted with medical document '{document_name}' in H3 cluster {h3_cluster}.",
            "user": session.get("username", "recipient_user"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        return jsonify({
            "status": "success",
            "request_id": req_id,
            "case_id": case_id,
            "status_text": "Pending",
            "h3_cluster": h3_cluster
        }), 201

    return jsonify({"status": "success", "requests": recipient_requests}), 200


@app.route("/api/v1/requests/nearby", methods=["GET"])
def api_nearby_requests():
    """Returns approved requests matching user vicinity cluster without raw coordinates."""
    h3_filter = request.args.get("h3")
    approved = [r for r in recipient_requests if r["status"] == "Approved"]
    if h3_filter:
        approved = [r for r in approved if r.get("h3_cluster") == h3_filter]

    # Verify that raw coordinates are NEVER exposed
    sanitized = []
    for r in approved:
        copy_r = dict(r)
        copy_r.pop("lat", None)
        copy_r.pop("lng", None)
        copy_r.pop("raw_coordinates", None)
        sanitized.append(copy_r)

    return jsonify({"status": "success", "requests": sanitized}), 200


@app.route("/api/v1/admin/adjudicate", methods=["POST"])
def api_admin_adjudicate():
    """District Administrator adjudication workflow with audit logging and push broadcast."""
    data = request.get_json() or {}
    req_id = data.get("request_id")
    action = data.get("action", "approve").lower()
    reason = data.get("reason", "Standard clinical review approval")

    target = next((r for r in recipient_requests if r["id"] == int(req_id)), None)
    if not target:
        return jsonify({"status": "error", "message": "Request not found"}), 404

    notifications_sent = 0
    if action == "approve":
        target["status"] = "Approved"
        target["adjudicated_by"] = session.get("username", "District Admin")
        target["adjudicated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Broadcast push notification to donors in the same H3 cluster
        cluster = target.get("h3_cluster", "872830828ffffff")
        notif = {
            "id": len(notifications_store) + 1,
            "title": f"Approved Blood Need: {target['blood_type']}",
            "message": f"Approved request {target['case_id']} ({target['donation_type']}) for donors in cluster {cluster}.",
            "h3_cluster": cluster,
            "blood_type": target["blood_type"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        notifications_store.append(notif)
        notifications_sent = len([d for d in donors if d.get("h3_cluster") == cluster])

        audit_logs.append({
            "action": "ADMIN ADJUDICATION: APPROVED",
            "details": f"District Admin approved request {target['case_id']}. Broadcast notification to donor cluster {cluster}.",
            "user": session.get("username", "District Admin"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    elif action == "reject":
        target["status"] = "Rejected"
        target["rejection_reason"] = reason
        target["adjudicated_by"] = session.get("username", "District Admin")
        target["adjudicated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        audit_logs.append({
            "action": "ADMIN ADJUDICATION: REJECTED",
            "details": f"District Admin rejected request {target['case_id']}. Reason: {reason}",
            "user": session.get("username", "District Admin"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    else:
        return jsonify({"status": "error", "message": "Invalid action. Use approve or reject."}), 400

    return jsonify({
        "status": "success",
        "request_id": target["id"],
        "case_id": target["case_id"],
        "new_status": target["status"],
        "notifications_sent": notifications_sent
    }), 200


@app.route("/api/v1/donations/log", methods=["POST"])
def api_log_donation():
    """Enforces 56-day cool-off period for whole blood and 14-day for platelets."""
    data = request.get_json() or {}
    donor_id = data.get("donor_id")
    donation_type = data.get("donation_type", "Whole Blood")
    date_str = data.get("donation_date", datetime.now().strftime("%Y-%m-%d"))

    donor = next((d for d in donors if d["username"] == donor_id), None)
    if not donor:
        return jsonify({"status": "error", "message": "Donor not found"}), 404

    try:
        new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Rule REQ-F-014: 56-day cool-off for whole blood
    # Rule REQ-F-015: 14-day cool-off for platelets
    required_cool_off_days = 56 if "whole" in donation_type.lower() else 14
    last_date_field = "last_whole_blood" if "whole" in donation_type.lower() else "last_platelets"
    
    last_donation_str = donor.get(last_date_field) or donor.get("last_donation")
    if last_donation_str:
        last_date = datetime.strptime(last_donation_str, "%Y-%m-%d").date()
        elapsed_days = (new_date - last_date).days
        if elapsed_days < required_cool_off_days:
            remaining = required_cool_off_days - elapsed_days
            eligible_date = last_date + timedelta(days=required_cool_off_days)
            return jsonify({
                "status": "error",
                "message": f"Mandatory cool-off period active. {remaining} day(s) remaining for {donation_type}.",
                "next_eligible_date": eligible_date.strftime("%Y-%m-%d"),
                "days_remaining": remaining
            }), 400

    # Update donor record
    donor[last_date_field] = date_str
    donor["last_donation"] = date_str
    donor["donation_count"] = donor.get("donation_count", 0) + 1

    next_eligible = new_date + timedelta(days=required_cool_off_days)

    audit_logs.append({
        "action": "DONATION LOGGED",
        "details": f"Donor {donor_id} logged {donation_type} donation. Next eligible date: {next_eligible.strftime('%Y-%m-%d')}.",
        "user": donor_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "status": "success",
        "message": "Donation logged successfully",
        "donation_count": donor["donation_count"],
        "next_eligible_date": next_eligible.strftime("%Y-%m-%d")
    }), 200


@app.route("/api/v1/gamification/badges")
def api_badges():
    username = session.get("username", "alex_doe")
    donor = next((d for d in donors if d["username"] == username), None)
    count = donor.get("donation_count", 5) if donor else 5

    badges = [
        {"name": "First Drop", "earned": count >= 1, "icon": "medal"},
        {"name": "Hero Donor", "earned": count >= 3, "icon": "trophy"},
        {"name": "Community Star", "earned": count >= 5, "icon": "star"},
        {"name": "Life Saver", "earned": count >= 7, "icon": "like"}
    ]

    return jsonify({
        "status": "success",
        "donor": username,
        "donation_count": count,
        "badges": badges
    }), 200


@app.route("/api/v1/notifications")
def api_notifications():
    return jsonify({"status": "success", "notifications": notifications_store}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
