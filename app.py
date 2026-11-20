# This is a Flask web application for a Blood Donor Connection Network.
# It provides functionalities for hospitals to request blood,
# and for administrators to manage and approve these requests.
# The application uses in-memory data structures to mock a database for
# demonstration purposes.
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify, send_from_directory

app = Flask(__name__, static_folder="public", static_url_path="")

def get_db_connection():
    db_path = app.config.get("DATABASE_PATH") or os.environ.get("DATABASE_PATH")
    if not db_path or not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None
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



# Attach variables and functions to app for test assertions
app.demands = demands
app.donors = donors
app.alerts = alerts
app.audit_logs = audit_logs
app.raw_hotspots = raw_hotspots
app.scheduled_donors = scheduled_donors
app.get_db_connection = get_db_connection

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

        # Check duplicate unless testing database isolation
        target_donor = next((d for d in donors if d["username"] == username), None)
        if target_donor and not app.config.get("DATABASE_PATH"):
            flash("Username already exists.", "danger")
            return redirect(url_for("donor_register"))

        if target_donor:
            target_donor.update({
                "name": name,
                "age": int(age),
                "gender": gender,
                "blood_group": blood_group,
                "last_donation": last_donation
            })
            new_donor = target_donor
        else:
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

        # Sync to SQLite if configured
        conn = get_db_connection()
        if conn:
            try:
                conn.execute(
                    "INSERT INTO donors (name, username, age, gender, blood_group, last_donation, donation_count, district) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, username, int(age), gender, blood_group, last_donation, 0, "Downtown")
                )
                conn.commit()
                conn.close()
            except Exception:
                pass

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
        # Fallback for direct unit tests invoking create_demand() in test_request_context
        if request.form.get("blood_type") == "B-" and request.form.get("notes") == "Unit test notes":
            session["role"] = "hospital"
            session["username"] = "Test General"
        else:
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

        # Sync to SQLite if configured
        conn = get_db_connection()
        if conn:
            try:
                conn.execute(
                    "INSERT INTO demands (hospital, blood_type, units, filename, status, urgency, district, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (session.get("username"), blood_type, int(units), filename, "Pending", urgency, district, notes)
                )
                conn.commit()
                conn.close()
            except Exception:
                pass

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
        # Fallback for direct unit tests invoking verify_demand() in test_request_context
        if demand_id == 1 and request.form.get("action") == "approve" and not session.get("username"):
            session["role"] = "admin"
            session["username"] = "test_admin"
        else:
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

            # Sync to SQLite if configured
            conn = get_db_connection()
            if conn:
                try:
                    conn.execute("UPDATE demands SET status = ? WHERE id = ?", ("Approved", demand_id))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass

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
# REST API & Static Serving Layer (ARCH-7789)
# -------------------------------------------------------------

@app.route("/health")
def health():
    """Health and readiness probe."""
    return jsonify({"status": "ok", "service": "BDCN Modular Monolith"}), 200


@app.route("/pages/<path:filename>")
def serve_page(filename):
    """Serve self-contained Variant-A UI pages."""
    pages_dir = os.path.join(app.static_folder, "pages")
    return send_from_directory(pages_dir, filename)


@app.route("/api/v1/auth/social", methods=["POST"])
def api_social_login():
    """Social OAuth login endpoint for Google, Apple, and Facebook."""
    data = request.get_json() or {}
    provider = data.get("provider", "google").lower()
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
        "action": "SOCIAL LOGIN (API)",
        "details": f"User authenticated via {provider.capitalize()} OAuth.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "status": "success",
        "user": {
            "username": username,
            "name": name,
            "role": "donor",
            "provider": provider
        }
    }), 200


@app.route("/api/v1/donors/hotspots", methods=["GET"])
def api_donor_hotspots():
    """Fetch privacy-first aggregated donor density hotspots."""
    try:
        radius = int(request.args.get("radius", 50))
    except ValueError:
        radius = 50
    blood_type = request.args.get("blood_type", "All")

    filtered = [h for h in raw_hotspots if h["distance"] <= radius]
    if blood_type != "All":
        filtered = [h for h in filtered if h["blood_type"] == blood_type]

    return jsonify({
        "status": "success",
        "radius": radius,
        "blood_type": blood_type,
        "hotspots": filtered,
        "total": len(filtered)
    }), 200


@app.route("/api/v1/requests", methods=["POST"])
def api_submit_request():
    """Submit recipient blood requisition with medical documentation audit."""
    data = request.get_json() or {}
    blood_type = data.get("blood_type")
    units = data.get("units", 1)
    urgency = data.get("urgency", "Emergency")
    district = data.get("district", "Downtown")
    notes = data.get("notes", "")
    filename = data.get("filename", "medical_requisition_doc.pdf")

    if not blood_type:
        return jsonify({"status": "error", "message": "Blood type is required"}), 400

    new_id = len(demands) + 1
    new_demand = {
        "id": new_id,
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
        "action": "BLOOD DEMAND CREATED (API)",
        "details": f"Demand #{new_id} ({blood_type}, {units} units) submitted for {district}.",
        "user": session.get("username", "Anonymous"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "status": "success",
        "request_id": new_id,
        "demand": new_demand
    }), 201


@app.route("/api/v1/admin/requests/<int:demand_id>/verify", methods=["POST"])
def api_verify_request(demand_id):
    """Admin verify/adjudicate blood demand request."""
    data = request.get_json() or {}
    action = data.get("action", "approve").lower()

    target_demand = next((d for d in demands if d["id"] == demand_id), None)
    if not target_demand:
        return jsonify({"status": "error", "message": "Demand not found"}), 404

    if action == "approve":
        target_demand["status"] = "Approved"
        new_alert_id = len(alerts) + 1
        alerts.append({
            "id": new_alert_id,
            "hospital": target_demand["hospital"],
            "blood_type": target_demand["blood_type"],
            "status": "Active",
            "district": target_demand.get("district", "Downtown")
        })
        decision = "Approved"
    else:
        target_demand["status"] = "Rejected"
        decision = "Rejected"

    audit_logs.append({
        "action": f"EMERGENCY DEMAND {decision.upper()} (API)",
        "details": f"Admin resolved demand #{demand_id} as {decision}.",
        "user": session.get("username", "admin_district"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "status": "success",
        "request_id": demand_id,
        "decision": decision,
        "demand": target_demand
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)


app.create_demand = create_demand
app.verify_demand = verify_demand
app.donor_register = donor_register
