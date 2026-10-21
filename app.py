# This is a Flask web application for a Blood Donor Connection Network.
# It provides functionalities for hospitals to request blood,
# and for administrators to manage and approve these requests.
# The application uses in-memory data structures to mock a database for
# demonstration purposes and is backed by ANSI SQL schemas in db/.
import os
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    url_for,
    jsonify,
    send_from_directory,
)

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "super-secret-bdcn-key-12345"
)

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
        "district": "Downtown",
        "patient_name": "Sarah Connor",
    },
    {
        "id": 2,
        "hospital": "General Hospital",
        "blood_type": "O-",
        "units": 4,
        "filename": "compliance_doc_B.pdf",
        "status": "Pending",
        "urgency": "Urgent",
        "district": "North District",
        "patient_name": "Marcus Wright",
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
        "id": 1,
        "name": "Jane Smith",
        "username": "janesmith",
        "age": 28,
        "gender": "Female",
        "blood_group": "O-",
        "last_donation": "2025-11-15",
        "donation_count": 5,
        "district": "Downtown",
        "coarse_lat": 37.77,
        "coarse_lng": -122.41,
        "distance_km": 2.5
    },
    {
        "id": 2,
        "name": "John Doe",
        "username": "johndoe",
        "age": 34,
        "gender": "Male",
        "blood_group": "A+",
        "last_donation": "2025-08-20",
        "donation_count": 2,
        "district": "North District",
        "coarse_lat": 37.79,
        "coarse_lng": -122.40,
        "distance_km": 5.1
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

notifications = [
    {
        "id": 1,
        "title": "Emergency Blood Request Dispatched",
        "message": "Demand #1 for A+ blood at General Hospital was approved by district admin.",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read": False
    },
    {
        "id": 2,
        "title": "Welcome to BDCN",
        "message": "Thank you for joining the Blood Donor Connection Network.",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read": True
    }
]


# ==============================================================================
# Health Probe
# ==============================================================================

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "bdcn-platform",
        "version": "1.0.0"
    }), 200


# ==============================================================================
# Static File Mount & Prototype UI Routes
# ==============================================================================

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)


@app.route("/ui/app")
@app.route("/ui/variant-a")
@app.route("/variant-a")
@app.route("/preview")
def ui_variant_a():
    return render_template("variant_a.html")


@app.route("/pages/<page>")
def serve_pages(page):
    if not page.endswith(".html"):
        page += ".html"
    return render_template(f"pages/{page}")


# ==============================================================================
# Legacy Web UI Routes (Fully Preserved for Backward Compatibility)
# ==============================================================================

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
            "id": len(donors) + 1,
            "name": name,
            "username": username,
            "age": 25,
            "gender": "Other",
            "blood_group": "O+",
            "last_donation": None,
            "donation_count": 1,
            "district": "Downtown",
            "coarse_lat": 37.77,
            "coarse_lng": -122.41,
            "distance_km": 3.0
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

        # Check duplicate
        if any(d["username"] == username for d in donors):
            flash("Username already exists.", "danger")
            return redirect(url_for("donor_register"))

        new_donor = {
            "id": len(donors) + 1,
            "name": name,
            "username": username,
            "age": int(age),
            "gender": gender,
            "blood_group": blood_group,
            "last_donation": last_donation,
            "donation_count": 0,
            "district": "Downtown",
            "coarse_lat": 37.77,
            "coarse_lng": -122.41,
            "distance_km": 4.0
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


# ==============================================================================
# REST API Endpoints (/api/v1) — Auth, Donors, Requests, Admin, Notifications
# ==============================================================================

@app.route("/api/v1/auth/social", methods=["POST"])
def api_auth_social():
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    provider = data.get("provider", "google").lower()
    email = data.get("email") or f"{provider}_user@bdcn.org"
    name = data.get("name") or f"Social {provider.capitalize()} User"
    username = f"social_{provider}_user"

    target_donor = next((d for d in donors if d["username"] == username), None)
    if not target_donor:
        target_donor = {
            "id": len(donors) + 1,
            "name": name,
            "username": username,
            "email": email,
            "age": 26,
            "gender": "Other",
            "blood_group": "O+",
            "last_donation": None,
            "donation_count": 1,
            "district": "Downtown",
            "coarse_lat": 37.77,
            "coarse_lng": -122.41,
            "distance_km": 3.0
        }
        donors.append(target_donor)

    session["username"] = username
    session["role"] = "donor"

    audit_logs.append({
        "action": "API SOCIAL LOGIN",
        "details": f"User authenticated via {provider}.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "authenticated": True,
        "user": {
            "username": username,
            "name": name,
            "email": email,
            "role": "donor"
        }
    }), 200


@app.route("/api/v1/auth/me", methods=["GET"])
def api_auth_me():
    if "username" in session:
        return jsonify({
            "authenticated": True,
            "user": {
                "username": session.get("username"),
                "role": session.get("role", "donor")
            }
        }), 200
    return jsonify({"authenticated": False, "user": None}), 200


@app.route("/api/v1/auth/logout", methods=["POST"])
def api_auth_logout():
    username = session.get("username", "Unknown")
    session.clear()
    audit_logs.append({
        "action": "API USER LOGOUT",
        "details": f"User '{username}' logged out via API.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return jsonify({"status": "logged_out"}), 200


@app.route("/api/v1/donors", methods=["GET"])
def api_get_donors():
    radius = float(request.args.get("radius", 50))
    blood_type = request.args.get("blood_type", "All")

    # Filter donors with privacy-safe coarse coordinates (REQ-N-003)
    results = []
    for d in donors:
        dist = d.get("distance_km", 5.0)
        bg = d.get("blood_group", "O+")
        if dist <= radius and (blood_type == "All" or bg == blood_type):
            results.append({
                "id": d.get("id", 1),
                "name": d.get("name"),
                "blood_group": bg,
                "district": d.get("district", "Downtown"),
                "distance_km": dist,
                # Coarse centroid coordinates (1.1km precision to protect privacy)
                "coarse_lat": round(d.get("coarse_lat", 37.77), 2),
                "coarse_lng": round(d.get("coarse_lng", -122.41), 2),
                "donation_count": d.get("donation_count", 0)
            })
    return jsonify(results), 200


@app.route("/api/v1/donors/profile", methods=["POST"])
def api_save_donor_profile():
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    full_name = data.get("full_name") or data.get("name", "Jane Smith")
    blood_type = data.get("blood_type") or data.get("blood_group", "O-")
    location = data.get("location") or data.get("district", "Downtown")
    email = data.get("email", "")
    phone = data.get("phone", "")

    username = session.get("username", "janesmith")
    target_donor = next((d for d in donors if d["username"] == username), None)
    if not target_donor:
        target_donor = {
            "id": len(donors) + 1,
            "name": full_name,
            "username": username,
            "blood_group": blood_type,
            "district": location,
            "email": email,
            "phone": phone,
            "donation_count": 1,
            "coarse_lat": 37.77,
            "coarse_lng": -122.41,
            "distance_km": 3.0
        }
        donors.append(target_donor)
    else:
        target_donor["name"] = full_name
        target_donor["blood_group"] = blood_type
        target_donor["district"] = location
        if email:
            target_donor["email"] = email
        if phone:
            target_donor["phone"] = phone

    audit_logs.append({
        "action": "API DONOR PROFILE UPDATED",
        "details": f"Donor profile updated for {username} ({blood_type}, {location}).",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "status": "success",
        "profile": {
            "full_name": full_name,
            "blood_type": blood_type,
            "location": location
        }
    }), 200


@app.route("/api/v1/donors/hotspots", methods=["GET"])
def api_get_hotspots():
    radius = int(request.args.get("radius", 50))
    blood_type = request.args.get("blood_type", "All")

    filtered = [h for h in raw_hotspots if h["distance"] <= radius]
    if blood_type != "All":
        filtered = [h for h in filtered if h["blood_type"] == blood_type]
    return jsonify(filtered), 200


@app.route("/api/v1/requests", methods=["GET", "POST"])
def api_requests():
    if request.method == "POST":
        # Supports JSON or multipart/form-data with file upload
        data = request.get_json(silent=True) or {}
        patient_name = data.get("patient_name") or request.form.get("patient_name", "Anonymous Patient")
        blood_type = data.get("blood_type") or request.form.get("blood_type", "O+")
        urgency = data.get("urgency") or request.form.get("urgency", "Emergency")
        hospital_name = data.get("hospital_name") or request.form.get("hospital_name", "General Hospital")
        district = data.get("district") or request.form.get("district", "Downtown")
        units = int(data.get("units") or request.form.get("units", 1))

        filename = "medical_necessity_doc.pdf"
        file = request.files.get("document") or request.files.get("verification_doc")
        if file and file.filename:
            filename = file.filename
        elif "document_name" in data:
            filename = data["document_name"]

        new_id = len(demands) + 1
        new_demand = {
            "id": new_id,
            "hospital": hospital_name,
            "patient_name": patient_name,
            "blood_type": blood_type,
            "units": units,
            "filename": filename,
            "status": "Pending",
            "urgency": urgency,
            "district": district
        }
        demands.append(new_demand)

        # Notify admin of new blood request
        notifications.insert(0, {
            "id": len(notifications) + 1,
            "title": f"New Blood Request #{new_id} ({blood_type})",
            "message": f"Submitted for {patient_name} at {hospital_name} with document '{filename}'.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "read": False
        })

        audit_logs.append({
            "action": "API BLOOD REQUEST CREATED",
            "details": f"Request #{new_id} ({blood_type}, {urgency}) created for {patient_name}. Doc: {filename}.",
            "user": session.get("username", "api_user"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        return jsonify({
            "id": new_id,
            "patient_name": patient_name,
            "blood_type": blood_type,
            "urgency": urgency,
            "hospital_name": hospital_name,
            "status": "Pending",
            "filename": filename
        }), 201

    # GET requests list
    status = request.args.get("status", "All")
    district = request.args.get("district", "All")
    results = [d for d in demands]
    if status != "All":
        results = [d for d in results if d.get("status") == status]
    if district != "All":
        results = [d for d in results if d.get("district") == district]

    return jsonify(results), 200


@app.route("/api/v1/admin/requests/<int:request_id>/verify", methods=["POST"])
def api_admin_verify(request_id):
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    action = data.get("action", "approve").lower()
    notes = data.get("notes", "")

    target_demand = next((d for d in demands if d["id"] == request_id), None)
    if not target_demand:
        return jsonify({"error": "Request not found"}), 404

    if action == "approve":
        target_demand["status"] = "Approved"
        new_alert_id = len(alerts) + 1
        alerts.append({
            "id": new_alert_id,
            "hospital": target_demand["hospital"],
            "blood_type": target_demand["blood_type"],
            "status": "Active"
        })
        notifications.insert(0, {
            "id": len(notifications) + 1,
            "title": f"Blood Request #{request_id} Approved",
            "message": f"District admin approved {target_demand['blood_type']} blood request. Dispatched to donors.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "read": False
        })
        audit_logs.append({
            "action": "API REQUEST APPROVED",
            "details": f"Request #{request_id} approved. Notes: {notes}",
            "user": session.get("username", "admin"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    elif action == "reject":
        target_demand["status"] = "Rejected"
        audit_logs.append({
            "action": "API REQUEST REJECTED",
            "details": f"Request #{request_id} rejected. Notes: {notes}",
            "user": session.get("username", "admin"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    else:
        return jsonify({"error": f"Invalid action: {action}"}), 400

    return jsonify({
        "id": request_id,
        "status": target_demand["status"],
        "message": f"Request #{request_id} successfully updated to {target_demand['status']}."
    }), 200


@app.route("/api/v1/donors/share", methods=["POST"])
def api_donors_share():
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    badge_name = data.get("badge_name", "Gold Guardian")
    platform = data.get("platform", "twitter")

    username = session.get("username", "voluntary_donor")
    audit_logs.append({
        "action": "API BADGE SHARED",
        "details": f"Donor '{username}' shared badge '{badge_name}' to {platform}.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    share_url = f"https://bdcn.org/share/badges/{badge_name.lower().replace(' ', '-')}"
    return jsonify({
        "status": "shared",
        "platform": platform,
        "share_url": share_url,
        "message": f"Successfully shared {badge_name} badge to {platform}!"
    }), 200


@app.route("/api/v1/notifications", methods=["GET"])
def api_get_notifications():
    return jsonify(notifications), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
