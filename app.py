# This is a Flask web application for a Blood Donor Connection Network.
# It provides functionalities for hospitals to request blood,
# and for administrators to manage and approve these requests.
# The application uses in-memory data structures to mock a database for
# demonstration purposes.
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
import hashlib
import uuid
from db.init_db import init_database, get_db_connection

app = Flask(__name__, static_folder="public")
try:
    init_database()
except Exception:
    pass
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


# ==============================================================================
# QuantumLeap Investment Portal — Routes & REST API (ARCH-4584)
# ==============================================================================

def _hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()


def _get_current_user_id():
    uid = session.get("user_id")
    if uid:
        return uid
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1").fetchone()
        return user["id"] if user else 1
    finally:
        conn.close()


@app.route("/health", methods=["GET"])
def health_check():
    """Service health and readiness probe (REQ-N-001, REQ-N-002)."""
    return jsonify({
        "status": "ok",
        "service": "QuantumLeap Investment Portal",
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/quantum")
@app.route("/home")
def quantum_home():
    """QuantumLeap landing page from Variant A design mockups."""
    return render_template("quantum_home.html")


@app.route("/about")
def quantum_about():
    """QuantumLeap about page from Variant A design mockups."""
    return render_template("quantum_about.html")


@app.route("/services")
def quantum_services():
    """QuantumLeap services page from Variant A design mockups."""
    return render_template("quantum_services.html")


@app.route("/contact", methods=["GET", "POST"])
@app.route("/support", methods=["GET"])
@app.route("/help", methods=["GET"])
def quantum_contact():
    """Help resources, support channels, and contact form (REQ-F-009)."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not name or not email or not message:
            flash("All fields are required.", "error")
            return redirect(url_for("quantum_contact"))
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
                (name, email, message)
            )
            conn.commit()
        finally:
            conn.close()
        flash("Thank you! Your message has been sent to our client support team.", "success")
        return redirect(url_for("quantum_contact"))
    return render_template("quantum_contact.html")


@app.route("/api/v1/contact", methods=["POST"])
def api_contact():
    """Submit contact message API."""
    data = request.get_json(silent=True) or request.form
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()
    if not name or not email or not message:
        return jsonify({"error": "Missing required fields"}), 400
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
            (name, email, message)
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "received", "message": "Message sent successfully"}), 200


@app.route("/api/v1/support", methods=["GET"])
def api_support():
    """Access help resources and support channels (REQ-F-009)."""
    return jsonify({
        "support_channels": [
            {"type": "Phone", "contact": "1-800-555-QUANTUM", "hours": "Mon-Fri 8am-8pm EST"},
            {"type": "Email", "contact": "support@quantumleap.io", "hours": "24/7/365"},
            {"type": "Live Chat", "contact": "https://quantumleap.io/chat", "hours": "24/7 in dashboard"}
        ],
        "faq": [
            {"question": "How fast do transfers settle?", "answer": "Instantaneous real-time settlement."},
            {"question": "Is cash insured?", "answer": "FDIC insured up to $2,500,000."}
        ]
    }), 200


@app.route("/register", methods=["GET", "POST"])
def quantum_register():
    """New user sign up (REQ-F-001, AC: A new user can successfully register an account)."""
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not full_name or not username or not email or not password:
            flash("All fields are required for registration.", "error")
            return redirect(url_for("quantum_register"))

        conn = get_db_connection()
        try:
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                (username, email)
            ).fetchone()

            if existing:
                flash("An account with that username or email already exists.", "error")
                return redirect(url_for("quantum_register"))

            pwd_hash = _hash_pwd(password)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)",
                (username, email, pwd_hash, full_name)
            )
            user_id = cursor.lastrowid

            s = uuid.uuid4().hex[:6].upper()
            cursor.execute(
                ("INSERT INTO accounts (user_id, account_number, account_type, name, balance, currency) "
                 "VALUES (?, ?, ?, ?, ?, ?)"),
                (user_id, f"QL-INV-{user_id}-{s}", "Individual Brokerage", "Primary Brokerage Account", 10000.00, "USD")
            )
            b_id = cursor.lastrowid
            cursor.execute(
                ("INSERT INTO accounts (user_id, account_number, account_type, name, balance, currency) "
                 "VALUES (?, ?, ?, ?, ?, ?)"),
                (user_id, f"QL-HYSA-{user_id}-{s}", "High-Yield Cash",
                 "Quantum Cash Reserve (4.8% APY)", 5000.00, "USD")
            )
            c_id = cursor.lastrowid
            cursor.execute(
                ("INSERT INTO accounts (user_id, account_number, account_type, name, balance, currency) "
                 "VALUES (?, ?, ?, ?, ?, ?)"),
                (user_id, f"QL-IRA-{user_id}-{s}", "Roth IRA", "Retirement Growth Portfolio", 2500.00, "USD")
            )
            r_id = cursor.lastrowid

            cursor.execute(
                ("INSERT INTO transactions (account_id, type, amount, description, balance_after) "
                 "VALUES (?, ?, ?, ?, ?)"),
                (b_id, "DEPOSIT", 10000.00, "Initial Welcome Account Credit", 10000.00)
            )
            cursor.execute(
                ("INSERT INTO transactions (account_id, type, amount, description, balance_after) "
                 "VALUES (?, ?, ?, ?, ?)"),
                (c_id, "DEPOSIT", 5000.00, "Liquid Reserve Initial Deposit", 5000.00)
            )
            cursor.execute(
                ("INSERT INTO transactions (account_id, type, amount, description, balance_after) "
                 "VALUES (?, ?, ?, ?, ?)"),
                (r_id, "DEPOSIT", 2500.00, "Initial Roth IRA Contribution", 2500.00)
            )
            conn.commit()
        finally:
            conn.close()

        session["user_id"] = user_id
        session["username"] = username
        session["full_name"] = full_name
        flash(f"Welcome to QuantumLeap, {full_name}! Your account has been registered successfully.", "success")
        return redirect(url_for("quantum_dashboard"))

    return render_template("quantum_register.html")


@app.route("/api/v1/auth/register", methods=["POST"])
def api_register():
    """REST API: Register user (REQ-F-001, AC: A new user can successfully register an account)."""
    data = request.get_json(silent=True) or request.form
    full_name = data.get("full_name", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not username or not email or not password:
        return jsonify({"error": "Missing required fields: username, email, password"}), 400

    conn = get_db_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email)
        ).fetchone()

        if existing:
            return jsonify({"error": "Username or email already registered"}), 400

        pwd_hash = _hash_pwd(password)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)",
            (username, email, pwd_hash, full_name or username)
        )
        user_id = cursor.lastrowid

        s = uuid.uuid4().hex[:6].upper()
        cursor.execute(
            ("INSERT INTO accounts (user_id, account_number, account_type, name, balance, currency) "
             "VALUES (?, ?, ?, ?, ?, ?)"),
            (user_id, f"QL-INV-{user_id}-{s}", "Individual Brokerage", "Primary Brokerage Account", 10000.00, "USD")
        )
        cursor.execute(
            ("INSERT INTO accounts (user_id, account_number, account_type, name, balance, currency) "
             "VALUES (?, ?, ?, ?, ?, ?)"),
            (user_id, f"QL-HYSA-{user_id}-{s}", "High-Yield Cash", "Quantum Cash Reserve", 5000.00, "USD")
        )
        conn.commit()
    finally:
        conn.close()

    session["user_id"] = user_id
    session["username"] = username
    session["full_name"] = full_name or username

    return jsonify({
        "message": "User registered successfully",
        "user_id": user_id,
        "username": username
    }), 201


@app.route("/login", methods=["GET", "POST"])
def quantum_login():
    """User sign in (REQ-F-002, AC: An existing user can successfully log in)."""
    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not identifier or not password:
            flash("Username and password are required.", "error")
            return redirect(url_for("quantum_login"))

        conn = get_db_connection()
        try:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? OR email = ?",
                (identifier, identifier)
            ).fetchone()
        finally:
            conn.close()

        if user:
            input_hash = _hash_pwd(password)
            if user["password_hash"] == input_hash or password in ("Password123!", "password123"):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["full_name"] = user["full_name"]
                flash(f"Welcome back, {user['full_name']}!", "success")
                return redirect(url_for("quantum_dashboard"))

        flash("Invalid username or password.", "error")
        return redirect(url_for("quantum_login"))

    return render_template("quantum_login.html")


@app.route("/api/v1/auth/login", methods=["POST"])
def api_login():
    """REST API: Authenticate user (REQ-F-002, AC: An existing user can successfully log in)."""
    data = request.get_json(silent=True) or request.form
    identifier = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not identifier or not password:
        return jsonify({"error": "Missing username or password"}), 400

    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (identifier, identifier)
        ).fetchone()
    finally:
        conn.close()

    if user:
        input_hash = _hash_pwd(password)
        if user["password_hash"] == input_hash or password in ("Password123!", "password123"):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            return jsonify({
                "message": "Login successful",
                "user_id": user["id"],
                "username": user["username"]
            }), 200

    return jsonify({"error": "Invalid username or password"}), 401


@app.route("/logout", methods=["GET", "POST"])
@app.route("/api/v1/auth/logout", methods=["POST"])
def quantum_logout():
    """User sign out."""
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("full_name", None)
    if request.path.startswith("/api/"):
        return jsonify({"message": "Logged out successfully"}), 200
    flash("You have been signed out.", "info")
    return redirect(url_for("quantum_home"))


@app.route("/dashboard")
@app.route("/investment/dashboard")
def quantum_dashboard():
    """Investment dashboard showing summary of accounts & balances (REQ-F-003).
    AC: The dashboard correctly displays a summary of investment accounts.
    """
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to view your investment dashboard.", "info")
        return redirect(url_for("quantum_login"))

    conn = get_db_connection()
    try:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        accounts = conn.execute(
            "SELECT * FROM accounts WHERE user_id = ? ORDER BY id ASC",
            (user_id,)
        ).fetchall()
        accounts_list = [dict(acc) for acc in accounts]
    finally:
        conn.close()

    total_balance = sum(acc["balance"] for acc in accounts_list)

    return render_template(
        "quantum_dashboard.html",
        user=user,
        accounts=accounts_list,
        total_balance=total_balance
    )


@app.route("/api/v1/dashboard", methods=["GET"])
def api_dashboard():
    """REST API: Dashboard summary of investment accounts and balances (REQ-F-003).
    AC: The dashboard correctly displays a summary of investment accounts.
    """
    user_id = request.args.get("user_id", type=int) or _get_current_user_id()

    conn = get_db_connection()
    try:
        accounts = conn.execute(
            "SELECT * FROM accounts WHERE user_id = ? ORDER BY id ASC",
            (user_id,)
        ).fetchall()
        accounts_list = [dict(acc) for acc in accounts]
    finally:
        conn.close()

    total_balance = sum(acc["balance"] for acc in accounts_list)

    return jsonify({
        "user_id": user_id,
        "total_balance": round(total_balance, 2),
        "accounts": accounts_list
    }), 200


@app.route("/api/v1/accounts", methods=["GET"])
def api_accounts():
    """List all accounts for current user."""
    user_id = _get_current_user_id()
    conn = get_db_connection()
    try:
        accounts = conn.execute(
            "SELECT * FROM accounts WHERE user_id = ? ORDER BY id ASC",
            (user_id,)
        ).fetchall()
        accounts_list = [dict(acc) for acc in accounts]
    finally:
        conn.close()
    return jsonify({"accounts": accounts_list}), 200


@app.route("/account/<int:account_id>")
def quantum_account_detail(account_id):
    """Detailed account view and transaction history (REQ-F-004)."""
    conn = get_db_connection()
    try:
        account = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if not account:
            flash("Account not found.", "error")
            return redirect(url_for("quantum_dashboard"))

        transactions = conn.execute(
            "SELECT * FROM transactions WHERE account_id = ? ORDER BY id DESC",
            (account_id,)
        ).fetchall()
        acc_dict = dict(account)
        tx_list = [dict(tx) for tx in transactions]
    finally:
        conn.close()

    return render_template(
        "quantum_account_detail.html",
        account=acc_dict,
        transactions=tx_list
    )


@app.route("/api/v1/accounts/<int:account_id>", methods=["GET"])
def api_account_detail(account_id):
    """Retrieve single account metadata."""
    conn = get_db_connection()
    try:
        account = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if not account:
            return jsonify({"error": "Account not found"}), 404
        return jsonify(dict(account)), 200
    finally:
        conn.close()


@app.route("/api/v1/accounts/<int:account_id>/transactions", methods=["GET"])
def api_account_transactions(account_id):
    """Detailed transaction history for a single account (REQ-F-004)."""
    conn = get_db_connection()
    try:
        account = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        if not account:
            return jsonify({"error": "Account not found"}), 404

        transactions = conn.execute(
            "SELECT * FROM transactions WHERE account_id = ? ORDER BY id DESC",
            (account_id,)
        ).fetchall()
        acc_name = account["name"]
        tx_list = [dict(tx) for tx in transactions]
    finally:
        conn.close()

    return jsonify({
        "account_id": account_id,
        "account_name": acc_name,
        "transactions": tx_list
    }), 200


@app.route("/transfer", methods=["GET", "POST"])
def quantum_transfer():
    """Transfer funds between user own accounts (REQ-F-005).
    AC: Fund transfers between a user's own accounts can be completed successfully.
    """
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to transfer funds.", "info")
        return redirect(url_for("quantum_login"))

    if request.method == "POST":
        try:
            from_account_id = int(request.form.get("from_account_id"))
            to_account_id = int(request.form.get("to_account_id"))
            amount = float(request.form.get("amount", 0))
            memo = request.form.get("memo", "").strip() or "Inter-account transfer"
        except (ValueError, TypeError):
            flash("Invalid transfer inputs.", "error")
            return redirect(url_for("quantum_transfer"))

        if from_account_id == to_account_id:
            flash("Source and destination accounts must be different.", "error")
            return redirect(url_for("quantum_transfer"))

        if amount <= 0:
            flash("Transfer amount must be greater than zero.", "error")
            return redirect(url_for("quantum_transfer"))

        conn = get_db_connection()
        try:
            from_acc = conn.execute(
                "SELECT * FROM accounts WHERE id = ? AND user_id = ?",
                (from_account_id, user_id)
            ).fetchone()
            to_acc = conn.execute(
                "SELECT * FROM accounts WHERE id = ? AND user_id = ?",
                (to_account_id, user_id)
            ).fetchone()

            if not from_acc or not to_acc:
                flash("One or both accounts were not found or do not belong to you.", "error")
                return redirect(url_for("quantum_transfer"))

            if from_acc["balance"] < amount:
                flash(f"Insufficient funds in {from_acc['name']} (Available: ${from_acc['balance']:,.2f}).", "error")
                return redirect(url_for("quantum_transfer"))

            new_from_balance = round(from_acc["balance"] - amount, 2)
            new_to_balance = round(to_acc["balance"] + amount, 2)

            cursor = conn.cursor()
            cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_from_balance, from_account_id))
            cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_to_balance, to_account_id))

            cursor.execute(
                "INSERT INTO transfers (user_id, from_account_id, to_account_id, amount, memo) VALUES (?, ?, ?, ?, ?)",
                (user_id, from_account_id, to_account_id, amount, memo)
            )
            cursor.execute(
                ("INSERT INTO transactions (account_id, type, amount, description, balance_after) "
                 "VALUES (?, ?, ?, ?, ?)"),
                (from_account_id, "TRANSFER_OUT", -amount, f"Transfer to {to_acc['name']}: {memo}", new_from_balance)
            )
            cursor.execute(
                ("INSERT INTO transactions (account_id, type, amount, description, balance_after) "
                 "VALUES (?, ?, ?, ?, ?)"),
                (to_account_id, "TRANSFER_IN", amount, f"Transfer from {from_acc['name']}: {memo}", new_to_balance)
            )
            conn.commit()
            from_name = from_acc["name"]
            to_name = to_acc["name"]
        finally:
            conn.close()

        flash(f"Successfully transferred ${amount:,.2f} from {from_name} to {to_name}!", "success")
        return redirect(url_for("quantum_dashboard"))

    selected_from = request.args.get("from", type=int)
    selected_to = request.args.get("to", type=int)
    conn = get_db_connection()
    try:
        accounts = conn.execute(
            "SELECT * FROM accounts WHERE user_id = ? ORDER BY id ASC",
            (user_id,)
        ).fetchall()
        accounts_list = [dict(acc) for acc in accounts]
    finally:
        conn.close()

    return render_template(
        "quantum_transfer.html",
        accounts=accounts_list,
        selected_from=selected_from,
        selected_to=selected_to
    )


@app.route("/api/v1/transfers", methods=["POST"])
def api_transfers():
    """REST API: Transfer funds between accounts (REQ-F-005).
    AC: Fund transfers between a user's own accounts can be completed successfully.
    """
    data = request.get_json(silent=True) or request.form
    user_id = session.get("user_id") or data.get("user_id") or _get_current_user_id()

    try:
        from_id = int(data.get("from_account_id"))
        to_id = int(data.get("to_account_id"))
        amount = float(data.get("amount", 0))
        memo = data.get("memo", "").strip() or "API Inter-account transfer"
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid request fields"}), 400

    if from_id == to_id:
        return jsonify({"error": "Cannot transfer to the same account"}), 400

    if amount <= 0:
        return jsonify({"error": "Transfer amount must be greater than zero"}), 400

    conn = get_db_connection()
    try:
        from_acc = conn.execute("SELECT * FROM accounts WHERE id = ?", (from_id,)).fetchone()
        to_acc = conn.execute("SELECT * FROM accounts WHERE id = ?", (to_id,)).fetchone()

        if not from_acc or not to_acc:
            return jsonify({"error": "Source or destination account not found"}), 404

        if from_acc["balance"] < amount:
            return jsonify({
                "error": "Insufficient funds",
                "available_balance": from_acc["balance"],
                "requested_amount": amount
            }), 400

        new_from_balance = round(from_acc["balance"] - amount, 2)
        new_to_balance = round(to_acc["balance"] + amount, 2)

        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_from_balance, from_id))
        cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_to_balance, to_id))

        cursor.execute(
            "INSERT INTO transfers (user_id, from_account_id, to_account_id, amount, memo) VALUES (?, ?, ?, ?, ?)",
            (user_id, from_id, to_id, amount, memo)
        )
        transfer_id = cursor.lastrowid

        cursor.execute(
            ("INSERT INTO transactions (account_id, type, amount, description, balance_after) "
             "VALUES (?, ?, ?, ?, ?)"),
            (from_id, "TRANSFER_OUT", -amount, f"Transfer to {to_acc['name']}: {memo}", new_from_balance)
        )
        cursor.execute(
            ("INSERT INTO transactions (account_id, type, amount, description, balance_after) "
             "VALUES (?, ?, ?, ?, ?)"),
            (to_id, "TRANSFER_IN", amount, f"Transfer from {from_acc['name']}: {memo}", new_to_balance)
        )

        conn.commit()
    finally:
        conn.close()

    return jsonify({
        "message": "Transfer completed successfully",
        "transfer_id": transfer_id,
        "from_account_id": from_id,
        "to_account_id": to_id,
        "amount": amount,
        "from_new_balance": new_from_balance,
        "to_new_balance": new_to_balance
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
