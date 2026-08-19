# This is a Flask web application for a Blood Donor Connection Network (BDCN).
# It provides functionalities for hospitals/recipients to request blood,
# administrators to manage and approve these requests,
# and donors to register, receive notifications, and accept requests.
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
)

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "super-secret-bdcn-key-12345"
)

# Blood type compatibility matrix (BR-001)
# Key: Donor blood type, Value: list of compatible recipient blood types
BLOOD_COMPATIBILITY = {
    "A+": ["A+", "AB+"],
    "A-": ["A+", "A-", "AB+", "AB-"],
    "B+": ["B+", "AB+"],
    "B-": ["B+", "B-", "AB+", "AB-"],
    "AB+": ["AB+"],
    "AB-": ["AB+", "AB-"],
    "O+": ["A+", "B+", "AB+", "O+"],
    "O-": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
}


def is_compatible(donor_blood: str, recipient_blood: str) -> bool:
    """Check if donor blood type is compatible with recipient blood type."""
    return recipient_blood in BLOOD_COMPATIBILITY.get(donor_blood, [])


# In-memory mock databases
demands = [
    {
        "id": 1,
        "hospital": "General Hospital",
        "facility_name": "General Hospital",
        "facility_location": "123 Medical Center Way, Downtown",
        "blood_type": "A+",
        "units": 10,
        "filename": "compliance_doc_A.pdf",
        "status": "Approved",
        "urgency": "Emergency",
        "district": "Downtown",
        "created_at": "2026-08-18 10:00:00",
        "accepted_by": [],
    },
    {
        "id": 2,
        "hospital": "General Hospital",
        "facility_name": "General Hospital",
        "facility_location": "123 Medical Center Way, Downtown",
        "blood_type": "O-",
        "units": 4,
        "filename": "compliance_doc_B.pdf",
        "status": "Pending",
        "urgency": "Urgent",
        "district": "North District",
        "created_at": "2026-08-18 11:30:00",
        "accepted_by": [],
    },
]

scheduled_donors = [
    {"name": "John Doe", "blood_type": "A+", "time": "10:30 AM"},
    {"name": "Jane Smith", "blood_type": "O-", "time": "02:15 PM"},
]

alerts = [
    {
        "id": 1,
        "hospital": "General Hospital",
        "blood_type": "A+",
        "status": "Active",
        "demand_id": 1,
        "district": "Downtown",
        "message": (
            "An urgent A+ donation is required within your district. "
            "Tap to view matched facility."
        ),
    }
]

donor_notifications: list[dict] = []

audit_logs = [
    {
        "action": "SYSTEM STARTUP",
        "details": "BDCN Core Platform service started successfully.",
        "user": "System",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    },
    {
        "action": "HOSPITAL DEMAND APPROVED",
        "details": "Demand #1 (A+, 10 units) approved. EmergencyDemandCreated event emitted.",
        "user": "admin_district",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    },
]

# Registered recipients
recipients = [
    {
        "username": "Mercy Hospital",
        "name": "Mercy Hospital",
        "role": "recipient",
        "facility_name": "Mercy General Hospital",
        "location": "456 Healthcare Blvd, Downtown",
    },
    {
        "username": "General Hospital",
        "name": "General Hospital",
        "role": "recipient",
        "facility_name": "General Hospital",
        "location": "123 Medical Center Way, Downtown",
    },
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
        "district": "Downtown",
    },
    {
        "name": "John Doe",
        "username": "johndoe",
        "age": 34,
        "gender": "Male",
        "blood_group": "A+",
        "last_donation": "2025-08-20",
        "donation_count": 2,
        "district": "North District",
    },
]

# Mock donor density hotspots
raw_hotspots = [
    {
        "district": "Downtown",
        "count": 24,
        "blood_type": "O-",
        "distance": 8,
        "top": 30,
        "left": 40,
    },
    {
        "district": "North District",
        "count": 15,
        "blood_type": "A+",
        "distance": 12,
        "top": 55,
        "left": 65,
    },
    {
        "district": "East Valley",
        "count": 8,
        "blood_type": "B+",
        "distance": 22,
        "top": 70,
        "left": 30,
    },
    {
        "district": "South Coast",
        "count": 19,
        "blood_type": "O+",
        "distance": 15,
        "top": 45,
        "left": 20,
    },
    {
        "district": "West Hills",
        "count": 11,
        "blood_type": "AB-",
        "distance": 35,
        "top": 20,
        "left": 80,
    },
]


def match_and_notify_donors(demand: dict) -> list:
    """Identify active, compatible donors and create notifications without recipient PII."""
    matched = []
    demand_blood = str(demand.get("blood_type", ""))
    demand_district = str(demand.get("district", "Downtown"))
    demand_id = demand.get("id")

    for donor in donors:
        donor_blood = str(donor.get("blood_group", ""))
        if is_compatible(donor_blood, demand_blood):
            matched.append(donor)
            notif_msg = (
                f"An urgent {demand_blood} donation is required within your district. "
                "Tap to view matched facility."
            )
            notification = {
                "id": len(donor_notifications) + 1,
                "donor_username": donor["username"],
                "demand_id": demand_id,
                "blood_type": demand_blood,
                "district": demand_district,
                "message": notif_msg,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Unread",
            }
            donor_notifications.append(notification)

    return matched


@app.route("/")
def home():
    if "username" in session:
        role = session.get("role")
        if role in ("hospital", "recipient"):
            return redirect(url_for("hospital_dashboard"))
        elif role == "admin":
            return redirect(url_for("admin_dashboard"))
        elif role == "donor":
            return redirect(url_for("donor_dashboard"))
    return redirect(url_for("login_hospital"))


@app.route("/landing")
def landing():
    return render_template("landing.html")


@app.route("/index")
def preview_index():
    return render_template("index.html")


def _process_admin_login(username: str):
    session["username"] = username
    session["role"] = "admin"
    audit_logs.append({
        "action": "ADMIN LOGIN",
        "details": f"Admin '{username}' logged in.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    flash("Welcome, Administrator!", "success")
    return redirect(url_for("admin_dashboard"))


def _process_recipient_login(username: str):
    session["username"] = username
    session["role"] = "recipient"
    if not any(r["username"] == username for r in recipients):
        recipients.append({
            "username": username,
            "name": username,
            "role": "recipient",
            "facility_name": f"{username} Clinic",
            "location": "Healthcare District",
        })
    audit_logs.append({
        "action": "RECIPIENT LOGIN",
        "details": f"Recipient/Hospital user '{username}' logged in.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    flash(f"Welcome, {username}!", "success")
    return redirect(url_for("hospital_dashboard"))


def _process_donor_login(username: str):
    session["username"] = username
    session["role"] = "donor"
    target_donor = next((d for d in donors if d["username"] == username), None)
    if not target_donor:
        target_donor = {
            "name": username.replace("_", " ").title(),
            "username": username,
            "age": 28,
            "gender": "Other",
            "blood_group": "O+",
            "last_donation": None,
            "donation_count": 1,
            "district": "Downtown",
        }
        donors.append(target_donor)
    audit_logs.append({
        "action": "DONOR LOGIN",
        "details": f"Donor '{username}' logged in.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    flash(f"Welcome back, {target_donor['name']}!", "success")
    return redirect(url_for("donor_dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login_unified():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", "donor")

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html")

        if role == "admin":
            return _process_admin_login(username)
        elif role in ("recipient", "hospital"):
            return _process_recipient_login(username)
        else:
            return _process_donor_login(username)

    return render_template("login.html")


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
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            flash("Logged in to Hospital Portal successfully!", "success")
            return redirect(url_for("hospital_dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("login_hospital.html")


@app.route("/login/recipient", methods=["GET", "POST"])
def login_recipient():
    return login_hospital()


@app.route("/login/donor", methods=["GET", "POST"])
def login_donor():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        target_donor = next(
            (d for d in donors if d["username"] == username), None
        )
        if target_donor and password:
            session["username"] = username
            session["role"] = "donor"
            audit_logs.append({
                "action": "DONOR LOGIN",
                "details": f"Donor '{username}' logged in successfully.",
                "user": username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
            "donation_count": 1,
            "district": "Downtown",
        }
        donors.append(target_donor)

    session["username"] = username
    session["role"] = "donor"

    audit_logs.append({
        "action": "SOCIAL LOGIN",
        "details": f"User logged in via {provider.capitalize()}.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    flash(
        f"Successfully authenticated via {provider.capitalize()}!",
        "success",
    )
    return redirect(url_for("donor_profile"))


@app.route("/register", methods=["GET", "POST"])
def register_unified():
    if request.method == "POST":
        role = request.form.get("role", "donor")
        username = request.form.get("username")
        name = request.form.get("name", username)
        blood_group = request.form.get("blood_group", "O+")
        district = request.form.get("district", "Downtown")

        if not username:
            flash("Username is required.", "danger")
            return render_template("login.html")

        if role in ("recipient", "hospital"):
            recipients.append({
                "username": username,
                "name": name,
                "role": "recipient",
                "facility_name": f"{name} Facility",
                "location": f"{district} Medical Center",
            })
            session["username"] = username
            session["role"] = "recipient"
            flash("Recipient registration successful!", "success")
            return redirect(url_for("hospital_dashboard"))
        elif role == "admin":
            session["username"] = username
            session["role"] = "admin"
            flash("Admin account created successfully!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            new_donor = {
                "name": name,
                "username": username,
                "age": int(request.form.get("age", 25)),
                "gender": request.form.get("gender", "Other"),
                "blood_group": blood_group,
                "last_donation": None,
                "donation_count": 0,
                "district": district,
            }
            donors.append(new_donor)
            session["username"] = username
            session["role"] = "donor"
            flash("Donor registration successful!", "success")
            return redirect(url_for("donor_dashboard"))

    return render_template("login.html")


@app.route("/donor/register", methods=["GET", "POST"])
def donor_register():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        age = request.form.get("age")
        gender = request.form.get("gender")
        blood_group = request.form.get("blood_group")
        last_donation = request.form.get("last_donation") or None
        district = request.form.get("district", "Downtown")

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
            "district": district,
        }
        donors.append(new_donor)

        audit_logs.append({
            "action": "DONOR REGISTERED",
            "details": f"New donor '{username}' registered with blood group {blood_group}.",
            "user": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

        session["username"] = username
        session["role"] = "donor"
        flash("Registration successful! Welcome to the BDCN family.", "success")
        return redirect(url_for("donor_profile"))

    return render_template("register_donor.html")


@app.route("/donor/dashboard")
def donor_dashboard():
    if session.get("role") != "donor":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_donor"))

    username = session.get("username")
    target_donor = next((d for d in donors if d["username"] == username), None)
    donor_blood = target_donor["blood_group"] if target_donor else "O+"

    my_notifications = [
        n for n in donor_notifications if n.get("donor_username") == username
    ]
    matched_demands = [
        d for d in demands
        if d.get("status") == "Approved" and is_compatible(donor_blood, d.get("blood_type", ""))
    ]

    return render_template(
        "donor-dashboard.html",
        donor=target_donor,
        notifications=my_notifications,
        matched_demands=matched_demands,
        demands=demands,
    )


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
            "earned": count >= 1,
        },
        {
            "name": "Silver Savior",
            "description": "Awarded for completing at least 3 voluntary donations.",
            "earned": count >= 3,
        },
        {
            "name": "Gold Guardian",
            "description": "Awarded for completing at least 5 voluntary donations.",
            "earned": count >= 5,
        },
    ]

    history = []
    if count > 0:
        history.append({
            "location": "Downtown Donation Center",
            "date": target_donor.get("last_donation") or "2025-11-15",
            "units": 1,
        })
    if count > 1:
        history.append({
            "location": "North District Clinic",
            "date": "2025-05-10",
            "units": 1,
        })

    return render_template(
        "donor_profile.html",
        donor=target_donor,
        badges=badges,
        history=history,
    )


@app.route("/donor/accept/<int:request_id>", methods=["GET", "POST"])
def donor_accept_request(request_id):
    """Allows a donor to accept a blood request, revealing facility location."""
    if session.get("role") != "donor":
        flash("Unauthorized. Please log in as a donor.", "danger")
        return redirect(url_for("login_donor"))

    username = session.get("username")
    target_demand = next((d for d in demands if d["id"] == request_id), None)

    if not target_demand:
        flash("Request not found.", "danger")
        return redirect(url_for("donor_dashboard"))

    if "accepted_by" not in target_demand:
        target_demand["accepted_by"] = []

    if username not in target_demand["accepted_by"]:
        target_demand["accepted_by"].append(username)

    facility_name = target_demand.get("facility_name", target_demand.get("hospital", "General Hospital"))
    facility_location = target_demand.get(
        "facility_location",
        f"{target_demand.get('district', 'Downtown')} Health Facility"
    )

    audit_logs.append({
        "action": "DONOR ACCEPTED REQUEST",
        "details": (
            f"Donor '{username}' accepted request #{request_id}. "
            f"Facility revealed: {facility_name} ({facility_location})."
        ),
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    flash(
        f"Request accepted! Please report to {facility_name} at {facility_location}.",
        "success",
    )

    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({
            "status": "SUCCESS",
            "message": "Donation request accepted successfully.",
            "facility_name": facility_name,
            "facility_location": facility_location,
            "blood_type": target_demand["blood_type"],
            "district": target_demand.get("district", "Downtown"),
        })

    return render_template(
        "alert-view.html",
        demand=target_demand,
        facility_name=facility_name,
        facility_location=facility_location,
        accepted=True,
    )


@app.route("/alert-view")
def alert_view():
    demand_id = request.args.get("demand_id", 1, type=int)
    target_demand = next((d for d in demands if d["id"] == demand_id), demands[0] if demands else None)
    facility_name = (
        target_demand.get("facility_name", target_demand.get("hospital", "General Hospital"))
        if target_demand else "General Hospital"
    )
    facility_location = (
        target_demand.get("facility_location", "Medical Center Way")
        if target_demand else "Downtown"
    )

    return render_template(
        "alert-view.html",
        demand=target_demand,
        facility_name=facility_name,
        facility_location=facility_location,
    )


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
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    flash(
        f"Successfully shared your {clean_badge} badge to your social profiles!",
        "success",
    )
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
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            flash("Logged in to Administrator Portal successfully!", "success")
            return redirect(url_for("admin_dashboard"))
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
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    flash("Logged out successfully.", "info")
    return redirect(url_for("login_hospital"))


@app.route("/hospital/dashboard")
def hospital_dashboard():
    if session.get("role") not in ("hospital", "recipient", "donor"):
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_hospital"))

    h_demands = [d for d in demands]
    return render_template(
        "dashboard.html",
        demands=h_demands,
        scheduled_donors=scheduled_donors,
    )


@app.route("/request-form", methods=["GET", "POST"])
@app.route("/recipient/request", methods=["GET", "POST"])
def request_form():
    """Recipient / Hospital blood request form with document upload."""
    if session.get("role") not in ("hospital", "recipient", "admin"):
        session["username"] = session.get("username", "Guest Recipient")
        session["role"] = "recipient"

    if request.method == "POST":
        blood_type = request.form.get("blood_type", "O+")
        units = request.form.get("units", "1")
        file = request.files.get("document") or request.files.get("medical_doc")
        hospital_location = request.form.get("hospital_location", "General Hospital Downtown")
        urgency = request.form.get("urgency", "Emergency")
        district = request.form.get("district", "Downtown")
        notes = request.form.get("notes", "")

        filename = file.filename if file and file.filename else "hospital_doc.pdf"
        new_id = len(demands) + 1

        new_demand = {
            "id": new_id,
            "hospital": session.get("username", "Recipient Hospital"),
            "facility_name": hospital_location,
            "facility_location": f"{hospital_location}, {district}",
            "blood_type": blood_type,
            "units": int(units) if str(units).isdigit() else 1,
            "filename": filename,
            "status": "Pending",
            "urgency": urgency,
            "district": district,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "accepted_by": [],
            "notes": notes,
        }
        demands.append(new_demand)

        audit_logs.append({
            "action": "BLOOD DEMAND CREATED",
            "details": (
                f"Demand #{new_id} ({blood_type}, {units} units) created for {district} "
                f"at {hospital_location}. Document: {filename}"
            ),
            "user": session.get("username"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

        flash(
            "Blood request submitted successfully and queued for admin verification!",
            "success",
        )
        return redirect(url_for("hospital_dashboard"))

    return render_template("request-form.html", demands=demands)


@app.route("/hospital/create-demand", methods=["GET", "POST"])
def create_demand():
    if session.get("role") != "hospital" and session.get("role") != "recipient":
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
                "danger",
            )
            return redirect(url_for("create_demand"))

        filename = file.filename
        new_id = len(demands) + 1
        new_demand = {
            "id": new_id,
            "hospital": session.get("username"),
            "facility_name": session.get("username"),
            "facility_location": f"{session.get('username')}, {district}",
            "blood_type": blood_type,
            "units": int(units),
            "filename": filename,
            "status": "Pending",
            "urgency": urgency,
            "district": district,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "accepted_by": [],
        }
        demands.append(new_demand)

        audit_logs.append({
            "action": "BLOOD DEMAND CREATED",
            "details": (
                f"Demand #{new_id} ({blood_type}, {units} units) created for {district} "
                f"with urgency {urgency}. File: {filename}. Notes: {notes}"
            ),
            "user": session.get("username"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

        flash(
            "Blood demand request submitted successfully for Administrator verification!",
            "success",
        )
        return redirect(url_for("hospital_dashboard"))

    return render_template("create_demand.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_admin"))

    pending_demands = [d for d in demands if d["status"] == "Pending"]
    approved_demands = [d for d in demands if d["status"] == "Approved"]
    rejected_demands = [d for d in demands if d["status"] == "Rejected"]

    return render_template(
        "admin-dashboard.html",
        pending_demands=pending_demands,
        approved_demands=approved_demands,
        rejected_demands=rejected_demands,
        alerts=alerts,
        demands=demands,
        donors=donors,
    )


@app.route("/admin/queue")
def admin_queue():
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_admin"))

    filter_district = request.args.get("filter_district", "All")
    pending_demands = [d for d in demands if d["status"] == "Pending"]
    if filter_district != "All":
        pending_demands = [
            d for d in pending_demands if d.get("district") == filter_district
        ]

    return render_template(
        "verification_queue.html",
        pending_demands=pending_demands,
        filter_district=filter_district,
    )


@app.route("/admin/verify/<int:demand_id>", methods=["POST"])
def verify_demand(demand_id):
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_admin"))

    action = request.form.get("action")
    target_demand = next((d for d in demands if d["id"] == demand_id), None)

    if target_demand:
        if action == "approve":
            target_demand["status"] = "Approved"

            new_alert_id = len(alerts) + 1
            alert_msg = (
                f"An urgent {target_demand['blood_type']} donation is required within your district. "
                "Tap to view matched facility."
            )
            alerts.append({
                "id": new_alert_id,
                "hospital": target_demand["hospital"],
                "blood_type": target_demand["blood_type"],
                "status": "Active",
                "demand_id": demand_id,
                "district": target_demand.get("district", "Downtown"),
                "message": alert_msg,
            })

            matched = match_and_notify_donors(target_demand)

            audit_logs.append({
                "action": "EMERGENCY DEMAND APPROVED",
                "details": (
                    f"Approved demand #{demand_id} ({target_demand['blood_type']}) "
                    f"for {target_demand.get('district', 'Downtown')}. Notified {len(matched)} matched donors."
                ),
                "user": session.get("username"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            flash(
                f"Approved demand #{demand_id}! Notified {len(matched)} matched donors.",
                "success",
            )
        elif action == "reject":
            target_demand["status"] = "Rejected"
            audit_logs.append({
                "action": "EMERGENCY DEMAND REJECTED",
                "details": f"Rejected demand #{demand_id} ({target_demand['blood_type']}).",
                "user": session.get("username"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            flash(f"Rejected demand #{demand_id}.", "warning")
    else:
        flash("Demand request not found.", "danger")

    return redirect(url_for("admin_dashboard"))


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
        audit_logs, key=lambda x: x["timestamp"], reverse=True
    )
    return render_template("audit_log.html", logs=sorted_logs)


@app.route("/map/hotspots")
def map_hotspots():
    radius = int(request.args.get("radius", 50))
    blood_type = request.args.get("blood_type", "All")

    filtered = [h for h in raw_hotspots if h["distance"] <= radius]
    if blood_type != "All":
        filtered = [h for h in filtered if h["blood_type"] == blood_type]

    return render_template(
        "map_hotspots.html",
        hotspots=filtered,
        radius=radius,
        blood_type=blood_type,
    )


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(port=5000, debug=debug_mode)
