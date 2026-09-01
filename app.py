# This is a Flask web application for a Blood Donor Connection Network.
# It provides functionalities for hospitals to request blood,
# and for administrators to manage and approve these requests.
# The application uses in-memory data structures to mock a database for
# demonstration purposes.
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, url_for

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "super-secret-bdcn-key-12345")

# In-memory mock databases
COMPATIBILITY_MATRIX = {
    "O-": ["O-"],
    "O+": ["O+", "O-"],
    "A-": ["A-", "O-"],
    "A+": ["A+", "A-", "O+", "O-"],
    "B-": ["B-", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "AB-": ["AB-", "A-", "B-", "O-"],
    "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"]
}

FACILITY_LOCATIONS = {
    "Downtown": {
        "name": "General Hospital - Downtown Medical Center",
        "address": "100 Medical Center Blvd, Downtown",
        "contact": "+1 (555) 019-2834",
        "coordinates": "37.7749, -122.4194"
    },
    "North District": {
        "name": "North District Memorial Hospital",
        "address": "450 North Bay Pkwy, North District",
        "contact": "+1 (555) 019-5821",
        "coordinates": "37.8044, -122.4089"
    },
    "East Valley": {
        "name": "East Valley Regional Healthcare",
        "address": "780 Valley View Rd, East Valley",
        "contact": "+1 (555) 019-9182",
        "coordinates": "37.7510, -122.3850"
    },
    "South Coast": {
        "name": "South Coast Community Clinic",
        "address": "320 Coastal Way, South Coast",
        "contact": "+1 (555) 019-4471",
        "coordinates": "37.7125, -122.4340"
    },
    "West Hills": {
        "name": "West Hills Urgent Care Hospital",
        "address": "900 Sunset Ridge, West Hills",
        "contact": "+1 (555) 019-3390",
        "coordinates": "37.7601, -122.4820"
    }
}


def get_compatible_donor_types(recipient_blood_type):
    """
    Returns the list of compatible donor blood types for a recipient according to BR-001.
    """
    return COMPATIBILITY_MATRIX.get(recipient_blood_type, [recipient_blood_type])


def find_matching_donors(blood_type, district=None):
    """
    Matches active donors with the requested blood type based on compatibility rules (REQ-F-010, REQ-F-011).
    """
    compatible_types = get_compatible_donor_types(blood_type)
    matched = [d for d in donors if d.get("blood_group") in compatible_types]
    return matched


VALID_BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
VALID_URGENCIES = ["Emergency", "Urgent", "Standard", "Routine"]
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "doc", "docx"}


def validate_blood_request(hospital, blood_type, units, filename=None, urgency="Standard", district="Downtown"):
    """
    Validates a recipient or hospital blood demand request.
    Enforces ABO/Rh blood group rules, positive unit counts, district presence, and document upload.
    Returns (is_valid, error_message, validated_dict).
    """
    if not hospital or not str(hospital).strip():
        return False, "Hospital or Recipient name is required.", None
    if not blood_type or blood_type not in VALID_BLOOD_GROUPS:
        return False, f"Invalid blood group '{blood_type}'. Must be one of {', '.join(VALID_BLOOD_GROUPS)}.", None
    try:
        units_int = int(units)
        if units_int <= 0:
            return False, "Units must be a positive integer greater than zero.", None
    except (ValueError, TypeError):
        return False, "Units must be a valid integer.", None
    if not district or not str(district).strip():
        return False, "District / Facility location is required.", None
    if not filename:
        return False, "Medical certification or hospital compliance document is required.", None

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid document format. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}.", None

    urgency_val = urgency if urgency in VALID_URGENCIES else "Standard"

    return True, "", {
        "hospital": hospital.strip(),
        "blood_type": blood_type,
        "units": units_int,
        "filename": filename,
        "urgency": urgency_val,
        "district": district.strip(),
        "status": "Pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


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
DISTRICT_CENTROIDS = {
    "Downtown": {"lat": 37.77, "lng": -122.41, "region": "Central Metro"},
    "North District": {"lat": 37.80, "lng": -122.40, "region": "North Bay"},
    "East Valley": {"lat": 37.75, "lng": -122.38, "region": "East Bay"},
    "South Coast": {"lat": 37.71, "lng": -122.43, "region": "South Peninsula"},
    "West Hills": {"lat": 37.76, "lng": -122.48, "region": "West Coast"}
}


def obfuscate_coordinates(lat, lng, max_decimals=2):
    """
    Rounds latitude and longitude to a maximum of 2 decimal places (~1.1km resolution)
    to prevent precision leakage and PII identification of donors (REQ-F-016, REQ-N-005).
    """
    try:
        f_lat = round(float(lat), max_decimals)
        f_lng = round(float(lng), max_decimals)
        return f_lat, f_lng
    except (ValueError, TypeError):
        return None, None


def sanitize_hotspots_for_client(hotspots_list, max_decimals=2):
    """
    Sanitizes geographic hotspot clusters for public and recipient client views.
    Ensures exact coordinates and donor PII are stripped, returning only regional centroids
    and aggregate counts (REQ-F-016, REQ-F-017, REQ-N-005).
    """
    sanitized = []
    for h in hotspots_list:
        district = h.get("district", "Unknown")
        centroid = DISTRICT_CENTROIDS.get(
            district,
            {"lat": 37.77, "lng": -122.42, "region": "General"}
        )
        obf_lat, obf_lng = obfuscate_coordinates(centroid["lat"], centroid["lng"], max_decimals)

        sanitized_item = {
            "district": district,
            "region": centroid["region"],
            "count": h.get("count", 0),
            "blood_type": h.get("blood_type", "All"),
            "distance": h.get("distance", 0),
            "centroid_lat": obf_lat,
            "centroid_lng": obf_lng,
            "top": h.get("top", 50),
            "left": h.get("left", 50),
            "precision_level": "regional_coarse_1km"
        }
        sanitized.append(sanitized_item)
    return sanitized


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
        hospital = session.get("username", "Mercy Hospital")

        filename = file.filename if file and file.filename else None

        is_valid, err, validated = validate_blood_request(
            hospital=hospital,
            blood_type=blood_type,
            units=units,
            filename=filename,
            urgency=urgency,
            district=district
        )

        if not is_valid:
            flash(err, "danger")
            return redirect(url_for("create_demand"))

        new_id = len(demands) + 1
        validated["id"] = new_id
        validated["notes"] = notes
        demands.append(validated)

        audit_logs.append({
            "action": "BLOOD DEMAND CREATED",
            "details": (
                f"Demand #{new_id} ({blood_type}, {units} units) created for {district} "
                f"with urgency {urgency}. File: {filename}. Notes: {notes}"
            ),
            "user": hospital,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        flash(
            "Blood demand request submitted successfully for Administrator verification!",
            "success")
        return redirect(url_for("hospital_dashboard"))

    return render_template("create_demand.html")


@app.route("/api/demands", methods=["GET", "POST"])
def api_demands():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict()
        file = request.files.get("document")
        filename = file.filename if file and file.filename else data.get("filename")
        hospital = data.get("hospital") or session.get("username", "Mercy Hospital")
        blood_type = data.get("blood_type")
        units = data.get("units")
        urgency = data.get("urgency", "Standard")
        district = data.get("district", "Downtown")
        notes = data.get("notes", "")

        is_valid, err, validated = validate_blood_request(
            hospital=hospital,
            blood_type=blood_type,
            units=units,
            filename=filename,
            urgency=urgency,
            district=district
        )
        if not is_valid:
            return {"status": "INVALID", "error": err}, 400

        new_id = len(demands) + 1
        validated["id"] = new_id
        validated["notes"] = notes
        demands.append(validated)

        audit_logs.append({
            "action": "API BLOOD DEMAND CREATED",
            "details": f"Demand #{new_id} ({blood_type}, {units} units) created via API for {district}.",
            "user": hospital,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return {"status": "SUCCESS", "demand": validated}, 201

    return {"status": "SUCCESS", "count": len(demands), "demands": demands}, 200


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
    blood_type = request.args.get("blood_type", "All").replace(" ", "+")

    # Filter density clusters by radius and blood type
    filtered = [h for h in raw_hotspots if h["distance"] <= radius]
    if blood_type != "All":
        filtered = [h for h in filtered if h["blood_type"] == blood_type]

    sanitized_hotspots = sanitize_hotspots_for_client(filtered)

    return render_template(
        "map_hotspots.html",
        hotspots=sanitized_hotspots,
        radius=radius,
        blood_type=blood_type
    )


@app.route("/api/map/hotspots", methods=["GET"])
def api_map_hotspots():
    radius = int(request.args.get("radius", 50))
    blood_type = request.args.get("blood_type", "All").replace(" ", "+")

    filtered = [h for h in raw_hotspots if h["distance"] <= radius]
    if blood_type != "All":
        filtered = [h for h in filtered if h["blood_type"] == blood_type]

    sanitized = sanitize_hotspots_for_client(filtered)
    return {
        "status": "SUCCESS",
        "radius_km": radius,
        "blood_type": blood_type,
        "clusters_count": len(sanitized),
        "clusters": sanitized
    }, 200


@app.route("/landing")
def landing_page():
    return render_template("landing.html")


@app.route("/login", methods=["GET", "POST"])
def login_unified():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", "donor").lower()

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("login.html")

        if role == "admin" or username.startswith("admin"):
            session["username"] = username
            session["role"] = "admin"
            flash("Logged in as Administrator.", "success")
            return redirect(url_for("admin_dashboard"))
        elif role in ["hospital", "recipient"] or "hospital" in username.lower():
            session["username"] = username
            session["role"] = "hospital"
            flash("Logged in as Hospital/Recipient.", "success")
            return redirect(url_for("hospital_dashboard"))
        else:
            # Donor login
            target = next((d for d in donors if d["username"] == username), None)
            if not target:
                # Auto register for test/demo ease
                target = {
                    "name": username.capitalize(),
                    "username": username,
                    "age": 26,
                    "gender": "Other",
                    "blood_group": "O+",
                    "last_donation": None,
                    "donation_count": 1
                }
                donors.append(target)
            session["username"] = username
            session["role"] = "donor"
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for("donor_dashboard"))

    return render_template("login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("login_admin"))

    pending = [d for d in demands if d["status"] == "Pending"]
    approved = [d for d in demands if d["status"] == "Approved"]
    return render_template(
        "admin_dashboard.html",
        pending_demands=pending,
        approved_demands=approved,
        alerts=alerts,
        total_donors=len(donors)
    )


@app.route("/donor/dashboard")
def donor_dashboard():
    if session.get("role") != "donor":
        flash("Donor access required.", "danger")
        return redirect(url_for("login_donor"))

    username = session.get("username")
    target_donor = next((d for d in donors if d["username"] == username), None)
    return render_template(
        "donor_dashboard.html",
        donor=target_donor,
        alerts=alerts,
        demands=demands
    )


@app.route("/alerts/view")
@app.route("/donor/alerts")
def alert_view():
    return render_template("alert_view.html", alerts=alerts, demands=demands)


@app.route("/request/form", methods=["GET", "POST"])
@app.route("/recipient/request", methods=["GET", "POST"])
def request_form_page():
    if request.method == "POST":
        return create_demand()
    return render_template("request_form.html")


@app.route("/donor/accept-request/<int:demand_id>", methods=["POST"])
def accept_request(demand_id):
    if session.get("role") != "donor":
        flash("Donor authorization required.", "danger")
        return redirect(url_for("login_donor"))

    target_demand = next((d for d in demands if d["id"] == demand_id), None)
    if not target_demand:
        flash("Blood request not found.", "danger")
        return redirect(url_for("donor_dashboard"))

    district = target_demand.get("district", "Downtown")
    facility = FACILITY_LOCATIONS.get(
        district,
        FACILITY_LOCATIONS["Downtown"]
    )

    donor_user = session.get("username", "anonymous_donor")
    target_demand["accepted_by"] = donor_user

    audit_logs.append({
        "action": "DONATION REQUEST ACCEPTED",
        "details": (
            f"Donor '{donor_user}' accepted demand #{demand_id} ({target_demand.get('blood_type')}). "
            f"Facility location revealed: {facility['name']}."
        ),
        "user": donor_user,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    flash(
        f"Thank you for accepting! Proceed to: {facility['name']} at {facility['address']}. "
        f"Contact: {facility['contact']}",
        "success"
    )
    return {
        "status": "SUCCESS",
        "message": "Request accepted",
        "facility": facility
    }, 200


@app.route("/api/matching/donors", methods=["GET"])
def api_matching_donors():
    blood_type = request.args.get("blood_type", "O+").replace(" ", "+")
    district = request.args.get("district")
    matched = find_matching_donors(blood_type, district)
    return {
        "status": "SUCCESS",
        "requested_blood_type": blood_type,
        "compatible_donor_types": get_compatible_donor_types(blood_type),
        "match_count": len(matched),
        "matched_donors": [
            {"username": d["username"], "blood_group": d["blood_group"]}
            for d in matched
        ]
    }, 200


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1")
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)
