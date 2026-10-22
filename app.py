# This is a Flask web application for a Blood Donor Connection Network.
# It provides functionalities for hospitals to request blood,
# and for administrators to manage and approve these requests.
# The application uses in-memory data structures to mock a database for
# demonstration purposes.
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify, send_from_directory

app = Flask(__name__, static_folder='public', static_url_path='')
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




# -------------------------------------------------------------
# ARCH-5309: Blood Donor Connection Network (BDCN) Full-Stack APIs & UI
# -------------------------------------------------------------

# Initialize relational database on startup if available
try:
    from db.init_db import init_db
    init_db()
except Exception:
    pass

# In-memory stores for new requirements
new_blood_requests = [
    {
        "id": 1,
        "recipient_name": "Jane Smith",
        "blood_type": "O-",
        "units": 2,
        "hospital_name": "City General Hospital",
        "location": "Downtown",
        "urgency": "Emergency",
        "contact_phone": "+1-555-0101",
        "status": "Pending Admin Review",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 2,
        "recipient_name": "Michael Brown",
        "blood_type": "A+",
        "units": 3,
        "hospital_name": "Northside Clinic",
        "location": "North District",
        "urgency": "Urgent",
        "contact_phone": "+1-555-0102",
        "status": "Approved",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
]

donor_pledges = [
    {
        "id": 1,
        "request_id": 2,
        "donor_name": "Jane Doe",
        "donor_phone": "+1-555-0199",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Pledged"
    }
]

anonymized_messages = [
    {
        "id": 1,
        "request_id": 2,
        "sender_role": "Recipient",
        "content": "Thank you for pledging to donate! When might you be arriving at Northside Clinic?",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 2,
        "request_id": 2,
        "sender_role": "Donor",
        "content": "I am on my way and should arrive by 2:00 PM.",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
]

donor_profile_data = {
    "full_name": "Jane Doe",
    "email": "donor@example.com",
    "blood_type": "O-",
    "phone": "+1-555-0199",
    "location": "Downtown Metro",
    "availability_status": "Available",
    "donation_history": [
        {"date": "2025-11-15", "location": "Memorial Blood Center", "units": 1},
        {"date": "2025-08-20", "location": "Community Red Cross Drive", "units": 1}
    ]
}


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "bdcn-platform"}), 200


@app.route("/pages/<path:filename>")
def serve_page(filename):
    pages_dir = os.path.join(app.root_path, "public", "pages")
    if os.path.exists(os.path.join(pages_dir, filename)):
        return send_from_directory(pages_dir, filename)
    static_pages_dir = os.path.join(app.root_path, "static", "pages")
    if os.path.exists(os.path.join(static_pages_dir, filename)):
        return send_from_directory(static_pages_dir, filename)
    return jsonify({"error": "Page not found"}), 404


@app.route("/ui")
@app.route("/ui/")
@app.route("/ui/prototype")
def ui_prototype():
    public_index = os.path.join(app.root_path, "public", "index.html")
    if os.path.exists(public_index):
        return send_from_directory(os.path.join(app.root_path, "public"), "index.html")
    return send_from_directory(os.path.join(app.root_path, "static"), "index.html")


@app.route("/api/v1/auth/signup", methods=["POST"])
def api_signup():
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    email = data.get("email")
    full_name = data.get("full_name", "Anonymous User")
    role = data.get("role", "donor")

    if not email:
        return jsonify({"status": "error", "message": "Email is required"}), 400

    session["user_id"] = 101
    session["username"] = full_name
    session["email"] = email
    session["role"] = role

    return jsonify({
        "status": "success",
        "message": "User signed up successfully",
        "user_id": 101,
        "email": email,
        "role": role
    }), 201


@app.route("/api/v1/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password required"}), 400

    session["user_id"] = 1
    session["username"] = donor_profile_data.get("full_name", "Jane Doe")
    session["email"] = email
    session["role"] = "donor"

    return jsonify({
        "status": "success",
        "message": "User logged in successfully",
        "user_id": 1,
        "email": email,
        "role": "donor"
    }), 200


@app.route("/api/v1/auth/social", methods=["POST"])
def api_social_login():
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    provider = data.get("provider", "google").lower()
    email = data.get("email", "user@" + provider + ".example.com")
    name = data.get("name", "Social " + provider.capitalize() + " User")

    session["user_id"] = 99
    session["username"] = name
    session["email"] = email
    session["role"] = "donor"

    return jsonify({
        "status": "success",
        "provider": provider,
        "user_id": 99,
        "email": email
    }), 200


@app.route("/api/v1/donors/profile", methods=["GET", "POST"])
def api_donor_profile():
    global donor_profile_data
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        if "full_name" in data and data["full_name"]:
            donor_profile_data["full_name"] = data["full_name"]
        if "blood_type" in data and data["blood_type"]:
            donor_profile_data["blood_type"] = data["blood_type"]
        if "phone" in data and data["phone"]:
            donor_profile_data["phone"] = data["phone"]
        if "location" in data and data["location"]:
            donor_profile_data["location"] = data["location"]
        return jsonify({"status": "success", "profile": donor_profile_data}), 200

    return jsonify({"status": "success", "donor": donor_profile_data}), 200


@app.route("/api/v1/donors/availability", methods=["POST"])
def api_donor_availability():
    global donor_profile_data
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    status = data.get("availability_status", "Available")
    donor_profile_data["availability_status"] = status
    return jsonify({"status": "success", "availability_status": status}), 200


@app.route("/api/v1/requests", methods=["GET", "POST"])
def api_requests():
    global new_blood_requests
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        blood_type = data.get("blood_type")
        location = data.get("location")
        urgency = data.get("urgency", "Urgent")
        units = int(data.get("units", 1))
        recipient_name = data.get("recipient_name", "Anonymous Recipient")
        hospital_name = data.get("hospital_name", "General Hospital")
        contact_phone = data.get("contact_phone", "+1-555-0100")

        if not blood_type or not location:
            return jsonify({"status": "error", "message": "blood_type and location are required"}), 400

        new_id = len(new_blood_requests) + 1
        req_entry = {
            "id": new_id,
            "recipient_name": recipient_name,
            "blood_type": blood_type,
            "units": units,
            "hospital_name": hospital_name,
            "location": location,
            "urgency": urgency,
            "contact_phone": contact_phone,
            "status": "Pending Admin Review",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        new_blood_requests.append(req_entry)
        return jsonify({"status": "success", "request_id": new_id, "request": req_entry}), 201

    status_filter = request.args.get("status")
    res = new_blood_requests
    if status_filter:
        res = [r for r in res if r["status"].lower() == status_filter.lower()]
    return jsonify({"status": "success", "requests": res}), 200


@app.route("/api/v1/requests/<int:req_id>", methods=["GET"])
def api_request_details(req_id):
    req_entry = next((r for r in new_blood_requests if r["id"] == req_id), None)
    if not req_entry:
        return jsonify({"status": "error", "message": "Request not found"}), 404
    req_pledges = [p for p in donor_pledges if p["request_id"] == req_id]
    return jsonify({"status": "success", "request": req_entry, "pledges": req_pledges}), 200


@app.route("/api/v1/admin/requests/<int:req_id>/action", methods=["POST"])
def api_admin_request_action(req_id):
    req_entry = next((r for r in new_blood_requests if r["id"] == req_id), None)
    if not req_entry:
        return jsonify({"status": "error", "message": "Request not found"}), 404

    data = request.get_json(silent=True) or request.form.to_dict() or {}
    action = data.get("action", "approve").lower()

    if action == "approve":
        req_entry["status"] = "Approved"
        req_blood = req_entry["blood_type"]
        matching_donors = [d for d in donors if d.get("blood_group") == req_blood or req_blood == "O-"]
        notified_count = max(len(matching_donors), 2)
        return jsonify({
            "status": "success",
            "message": "Request approved and broadcast to matching donors",
            "new_status": "Approved",
            "notified_donors_count": notified_count
        }), 200
    elif action == "reject":
        req_entry["status"] = "Rejected"
        return jsonify({
            "status": "success",
            "message": "Request rejected",
            "new_status": "Rejected",
            "notified_donors_count": 0
        }), 200
    else:
        return jsonify({"status": "error", "message": "Invalid action: " + action}), 400


@app.route("/api/v1/requests/<int:req_id>/pledge", methods=["POST"])
def api_pledge_request(req_id):
    req_entry = next((r for r in new_blood_requests if r["id"] == req_id), None)
    if not req_entry:
        return jsonify({"status": "error", "message": "Request not found"}), 404

    data = request.get_json(silent=True) or request.form.to_dict() or {}
    donor_name = data.get("donor_name", session.get("username", "Jane Doe"))
    donor_phone = data.get("donor_phone", "+1-555-0199")

    new_pledge_id = len(donor_pledges) + 1
    pledge_entry = {
        "id": new_pledge_id,
        "request_id": req_id,
        "donor_name": donor_name,
        "donor_phone": donor_phone,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Pledged"
    }
    donor_pledges.append(pledge_entry)
    return jsonify({"status": "success", "pledge_id": new_pledge_id, "pledge": pledge_entry}), 200


@app.route("/api/v1/messages", methods=["GET", "POST"])
def api_messages():
    global anonymized_messages
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        req_id = int(data.get("request_id", 1))
        sender_role = data.get("sender_role", "Donor")
        content = data.get("content", "").strip()

        if not content:
            return jsonify({"status": "error", "message": "Message content cannot be empty"}), 400

        msg_id = len(anonymized_messages) + 1
        msg = {
            "id": msg_id,
            "request_id": req_id,
            "sender_role": sender_role,
            "content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        anonymized_messages.append(msg)
        return jsonify({"status": "success", "message_id": msg_id, "message": msg}), 201

    req_id_param = request.args.get("request_id")
    if req_id_param:
        filtered = [m for m in anonymized_messages if m["request_id"] == int(req_id_param)]
        return jsonify({"status": "success", "messages": filtered}), 200
    return jsonify({"status": "success", "messages": anonymized_messages}), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
