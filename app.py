# This is a Flask web application for a Blood Donor Connection Network.
# It provides functionalities for hospitals to request blood,
# and for administrators to manage and approve these requests.
# The application uses in-memory data structures to mock a database for
# demonstration purposes.
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify

app = Flask(__name__)
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
        "district": "Downtown",
        "recipient": "General Hospital"
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
        "recipient": "General Hospital"
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

# In-memory recipients
recipients = [
    {
        "username": "recipient_user",
        "name": "Alex Taylor",
        "blood_group": "A+"
    }
]

# Blood compatibility matrix (BR-001)
COMPATIBILITY_MAP = {
    "O-": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],  # Universal Red Cell Donor
    "O+": ["O+", "A+", "B+", "AB+"],
    "A-": ["A-", "A+", "AB-", "AB+"],
    "A+": ["A+", "AB+"],
    "B-": ["B-", "B+", "AB-", "AB+"],
    "B+": ["B+", "AB+"],
    "AB-": ["AB-", "AB+"],
    "AB+": ["AB+"]
}

# Mock donor density hotspots
raw_hotspots = [
    {"district": "Downtown", "count": 24, "blood_type": "O-", "distance": 8, "top": 30, "left": 40},
    {"district": "North District", "count": 15, "blood_type": "A+", "distance": 12, "top": 55, "left": 65},
    {"district": "East Valley", "count": 8, "blood_type": "B+", "distance": 22, "top": 70, "left": 30},
    {"district": "South Coast", "count": 19, "blood_type": "O+", "distance": 15, "top": 45, "left": 20},
    {"district": "West Hills", "count": 11, "blood_type": "AB-", "distance": 35, "top": 20, "left": 80}
]


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "bdcn_platform"}), 200


@app.route("/")
def home():
    if "username" in session:
        role = session.get("role")
        if role == "hospital":
            return redirect(url_for("hospital_dashboard"))
        elif role == "admin":
            return redirect(url_for("admin_dashboard"))
        elif role == "donor":
            return redirect(url_for("donor_dashboard"))
        elif role == "recipient":
            return redirect(url_for("recipient_dashboard"))
    return redirect(url_for("login_hospital"))


# Dedicated Unified Login Page (ARCH-6455 REQ-F-001)
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", "donor")

        if not username or not password:
            flash("Please provide both username and password.", "danger")
            return render_template("login.html"), 400

        session["username"] = username
        session["role"] = role

        audit_logs.append({
            "action": "PORTAL LOGIN",
            "details": f"User '{username}' logged in successfully with role '{role}'.",
            "user": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        flash(f"Welcome to BDCN, {username}!", "success")

        if role == "donor":
            return redirect(url_for("donor_dashboard"))
        elif role == "recipient":
            return redirect(url_for("recipient_dashboard"))
        elif role == "hospital":
            return redirect(url_for("admin_dashboard"))
        elif role == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("home"))

    return render_template("login.html")


# REST API Auth Login (ARCH-6455 OAuth2 & Session)
@app.route("/api/v1/auth/login", methods=["POST"])
def api_auth_login():
    data = request.get_json(silent=True) or request.form
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "donor")

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password required"}), 400

    session["username"] = username
    session["role"] = role

    audit_logs.append({
        "action": "API LOGIN",
        "details": f"User '{username}' authenticated via API with role '{role}'.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    redirect_target = "/donor/dashboard"
    if role == "recipient":
        redirect_target = "/recipient/dashboard"
    elif role == "hospital":
        redirect_target = "/hospital/dashboard"
    elif role == "admin":
        redirect_target = "/admin/dashboard"

    return jsonify({
        "success": True,
        "username": username,
        "role": role,
        "redirect_url": redirect_target
    }), 200


# REST API OAuth2 Session Endpoint
@app.route("/api/v1/auth/oauth2", methods=["POST"])
def api_auth_oauth2():
    data = request.get_json(silent=True) or request.form
    provider = data.get("provider", "google")
    role = data.get("role", "donor")

    username = f"oauth2_{provider}_user"
    session["username"] = username
    session["role"] = role

    audit_logs.append({
        "action": "OAUTH2 SESSION CREATED",
        "details": f"OAuth2 session created via provider '{provider}' for role '{role}'.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    redirect_target = "/donor/dashboard" if role == "donor" else f"/{role}/dashboard"
    return jsonify({
        "success": True,
        "username": username,
        "role": role,
        "redirect_url": redirect_target
    }), 200


# Role-Based Blood Requests API (ARCH-6455 Filtering)
@app.route("/api/v1/requests", methods=["GET", "POST"])
def api_requests():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        blood_type = data.get("blood_type", "O+")
        units = int(data.get("units", 1))
        urgency = data.get("urgency", "Urgent")
        district = data.get("district", "Downtown")

        new_id = len(demands) + 1
        username = session.get("username", "api_user")
        new_demand = {
            "id": new_id,
            "hospital": username if session.get("role") == "hospital" else "City General Hospital",
            "blood_type": blood_type,
            "units": units,
            "filename": "clinical_note.pdf",
            "status": "Pending",
            "urgency": urgency,
            "district": district,
            "recipient": username
        }
        demands.append(new_demand)
        return jsonify({"id": new_id, "status": "Pending", "message": "Blood request created"}), 201

    # Role-based filtering
    requested_role = request.args.get("role") or session.get("role", "donor")
    status_filter = request.args.get("status")
    blood_filter = request.args.get("blood_type")

    filtered = [d for d in demands]

    if requested_role == "donor":
        # Determine donor blood type
        user = session.get("username")
        donor_obj = next((d for d in donors if d["username"] == user), None)
        donor_group = donor_obj["blood_group"] if donor_obj else "O-"
        # A request needs blood_type T. Can donor donate to T?
        compatible_targets = COMPATIBILITY_MAP.get(donor_group, [donor_group])
        filtered = [d for d in filtered if d.get("blood_type") in compatible_targets]
    elif requested_role == "recipient":
        user = session.get("username")
        filtered = [d for d in filtered if d.get("recipient") == user or d.get("hospital") == user]
    # For hospital or admin, all demands are accessible for full supply chain management

    if status_filter:
        filtered = [d for d in filtered if d.get("status") == status_filter]
    if blood_filter:
        filtered = [d for d in filtered if d.get("blood_type") == blood_filter]

    return jsonify({"role": requested_role, "requests": filtered}), 200


# Donor Dashboard (ARCH-6455 REQ-F-002)
@app.route("/donor/dashboard")
def donor_dashboard():
    if session.get("role") != "donor":
        # Fallback if not logged in
        session["username"] = session.get("username", "janesmith")
        session["role"] = "donor"

    username = session.get("username")
    target_donor = next((d for d in donors if d["username"] == username), None)
    donor_group = target_donor["blood_group"] if target_donor else "O-"

    compatible_targets = COMPATIBILITY_MAP.get(donor_group, [donor_group])
    compatible_requests = [d for d in demands if d.get("blood_type") in compatible_targets]

    return render_template(
        "donor_dashboard.html",
        donor=target_donor,
        compatible_requests=compatible_requests
    )


# Recipient Dashboard (ARCH-6455 REQ-F-003)
@app.route("/recipient/dashboard")
def recipient_dashboard():
    if session.get("role") != "recipient":
        session["username"] = session.get("username", "recipient_user")
        session["role"] = "recipient"

    username = session.get("username")
    # Show requests submitted by recipient or hospital matching user
    recipient_requests = [d for d in demands if d.get("recipient") == username or d.get("hospital") == username]
    if not recipient_requests:
        recipient_requests = [d for d in demands]  # Display all as demo if none specifically owned

    return render_template(
        "recipient_dashboard.html",
        recipient_requests=recipient_requests
    )


@app.route("/recipient/create-request", methods=["POST"])
def recipient_create_request():
    blood_type = request.form.get("blood_type")
    units = request.form.get("units", 1)
    urgency = request.form.get("urgency", "Urgent")
    district = request.form.get("district", "Downtown")
    username = session.get("username", "recipient_user")

    new_id = len(demands) + 1
    new_demand = {
        "id": new_id,
        "hospital": f"Clinic for {username}",
        "blood_type": blood_type,
        "units": int(units),
        "filename": "requisition.pdf",
        "status": "Pending",
        "urgency": urgency,
        "district": district,
        "recipient": username
    }
    demands.append(new_demand)

    audit_logs.append({
        "action": "RECIPIENT BLOOD REQUEST CREATED",
        "details": f"Request #{new_id} created by recipient {username} for {blood_type} ({units} units).",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    flash("Blood request submitted successfully and queued for review!", "success")
    return redirect(url_for("recipient_dashboard"))


# Hospital Admin Dashboard (ARCH-6455 REQ-F-004)
@app.route("/admin/dashboard")
@app.route("/hospital/admin-dashboard")
def admin_dashboard():
    if session.get("role") not in ["admin", "hospital"]:
        session["username"] = session.get("username", "admin_district")
        session["role"] = "admin"

    pending_count = len([d for d in demands if d.get("status") == "Pending"])
    emergency_count = len([d for d in demands if d.get("urgency") == "Emergency"])

    return render_template(
        "hospital_admin_dashboard.html",
        demands=demands,
        pending_count=pending_count,
        emergency_count=emergency_count,
        donors=donors
    )


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
    return redirect(url_for("donor_dashboard"))


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
        return redirect(url_for("donor_dashboard"))

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

    return render_template("donor_profile.html", donor=target_donor, badges=badges, history=history)


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
    if session.get("role") != "hospital" and session.get("role") != "donor" and session.get("role") != "admin":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_hospital"))

    h_demands = [d for d in demands]
    return render_template("dashboard.html", demands=h_demands, scheduled_donors=scheduled_donors)


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
            "district": district,
            "recipient": session.get("username")
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

    return render_template("verification_queue.html", pending_demands=pending_demands, filter_district=filter_district)


@app.route("/admin/verify/<int:demand_id>", methods=["POST"])
def verify_demand(demand_id):
    if session.get("role") != "admin" and session.get("role") != "hospital":
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

    if session.get("role") == "hospital":
        return redirect(url_for("admin_dashboard"))
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

    sorted_logs = sorted(audit_logs, key=lambda x: x["timestamp"], reverse=True)
    return render_template("audit_log.html", logs=sorted_logs)


@app.route("/map/hotspots")
def map_hotspots():
    radius = int(request.args.get("radius", 50))
    blood_type = request.args.get("blood_type", "All")

    filtered = [h for h in raw_hotspots if h["distance"] <= radius]
    if blood_type != "All":
        filtered = [h for h in filtered if h["blood_type"] == blood_type]

    return render_template("map_hotspots.html", hotspots=filtered, radius=radius, blood_type=blood_type)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
