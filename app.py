# This is a Flask web application for a Blood Donor Connection Network.
# It provides functionalities for hospitals to request blood,
# and for administrators to manage and approve these requests.
# The application uses in-memory data structures to mock a database for
# demonstration purposes, backed by ANSI SQL SQLite schema for persistence.
import os
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, session,
    flash, url_for, jsonify, send_from_directory, abort
)

# 12-Factor Configuration & Local Infrastructure
FLASK_SECRET_KEY = os.environ.get(
    "FLASK_SECRET_KEY",
    "super-secret-bdcn-key-12345"
)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///app.db")
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "persistent-genai")
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "persistent-genai-tf-state")
REMINDER_THRESHOLD_HOURS = float(os.environ.get("REMINDER_THRESHOLD_HOURS", 2.0))
PORT = int(os.environ.get("PORT", 5000))
HOST = os.environ.get("HOST", "0.0.0.0")

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = FLASK_SECRET_KEY

# Initialize database schema and seeds
try:
    from db.init_db import init_database
    init_database()
except Exception:
    pass

# In-memory mock databases (Legacy & Multi-Tier support)
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
        "location": "Oakland, CA",
        "available": True,
        "last_donation": "2025-11-15",
        "donation_count": 5
    },
    {
        "name": "John Doe",
        "username": "johndoe",
        "age": 34,
        "gender": "Male",
        "blood_group": "O-",
        "location": "San Francisco, CA",
        "available": True,
        "last_donation": "2025-08-20",
        "donation_count": 2
    }
]

# Connection Requests (REQ-F-005, REQ-F-006, REQ-F-008)
connection_requests = [
    {
        "request_id": "REQ-10234",
        "recipient_id": "REC-9876",
        "blood_type": "O-",
        "location": "San Francisco, CA",
        "message": "Urgent need for scheduled surgery patient letter enclosed.",
        "document_name": "hospital_letter.pdf",
        "document_base64": "",
        "status": "Pending",
        "submitted_at": (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
        "hours_pending": 3.0,
        "reminder_active": True,
        "verified_by": None,
        "verified_at": None,
        "notes": ""
    },
    {
        "request_id": "REQ-10233",
        "recipient_id": "REC-9875",
        "blood_type": "A+",
        "location": "Oakland, CA",
        "message": "Platelet and whole blood requirement.",
        "document_name": "clinic_requisition.pdf",
        "document_base64": "",
        "status": "Pending",
        "submitted_at": (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
        "hours_pending": 0.5,
        "reminder_active": False,
        "verified_by": None,
        "verified_at": None,
        "notes": ""
    },
    {
        "request_id": "REQ-10232",
        "recipient_id": "REC-9870",
        "blood_type": "B+",
        "location": "San Jose, CA",
        "message": "Regular transfusion support.",
        "document_name": "medical_necessity_cert.pdf",
        "document_base64": "",
        "status": "Approved",
        "submitted_at": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "hours_pending": 24.0,
        "reminder_active": False,
        "verified_by": "admin_district",
        "verified_at": (datetime.now() - timedelta(hours=22)).strftime("%Y-%m-%d %H:%M:%S"),
        "notes": "Approved valid requisition."
    }
]

app_notifications = [
    {
        "id": 1,
        "user_id": "admin",
        "title": "Urgent Reminder: Pending Request REQ-10234",
        "message": "Request REQ-10234 has been pending review for over 2 hours.",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read": False
    },
    {
        "id": 2,
        "user_id": "REC-9876",
        "title": "Request Received",
        "message": "Your connection request REQ-10234 was submitted and is pending administrator review.",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read": True
    }
]

# Mock donor density hotspots (Centroids masked to prevent exact address leakage)
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


# -------------------------------------------------------------
# Static Asset Serving & UI Page Mounts (Full-Stack Harness)
# -------------------------------------------------------------
@app.route("/static/<path:filename>")
def serve_static_asset(filename):
    return send_from_directory("static", filename)


@app.route("/pages/<path:page_name>")
def serve_ui_page(page_name):
    template_path = f"pages/{page_name}"
    try:
        return render_template(template_path)
    except Exception:
        abort(404)


@app.route("/login")
def ui_login():
    return render_template("pages/login.html")


@app.route("/donor-dashboard")
def ui_donor_dashboard():
    return render_template("pages/donor-dashboard.html")


@app.route("/recipient-search")
def ui_recipient_search():
    return render_template("pages/recipient-search.html")


@app.route("/request-form")
def ui_request_form():
    return render_template("pages/request-form.html")


@app.route("/admin-dashboard")
def ui_admin_dashboard():
    return render_template("pages/admin-dashboard.html")


@app.route("/admin-request-details")
def ui_admin_request_details():
    req_id = request.args.get("id", "REQ-10234")
    return render_template("pages/admin-request-details.html", req_id=req_id)


@app.route("/ui/app")
@app.route("/preview")
def ui_app_hub():
    return render_template("pages/index.html")


# -------------------------------------------------------------
# REST API Endpoints (api_contract.json)
# -------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "blood_donor_conn_net",
        "version": "1.0.0"
    }), 200


@app.route("/api/v1/auth/social", methods=["POST"])
def api_auth_social():
    # REQ-F-001 / AC 1: Social authentication via Google, Apple, or Facebook
    data = request.get_json(silent=True) or {}
    provider = data.get("provider", "Google")
    email = data.get("email") or f"{provider.lower()}.user@example.com"
    name = data.get("name") or f"{provider} User"
    role = data.get("role", "donor")

    session["username"] = email.split("@")[0]
    session["role"] = role

    audit_logs.append({
        "action": "API SOCIAL LOGIN",
        "details": f"User authenticated via {provider} ({email}).",
        "user": session["username"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "authenticated": True,
        "user_id": f"USR-{abs(hash(email)) % 10000}",
        "email": email,
        "name": name,
        "role": role,
        "provider": provider
    }), 200


@app.route("/api/v1/auth/login", methods=["POST"])
def api_auth_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "donor@example.com")
    role = data.get("role", "donor")
    session["username"] = email.split("@")[0]
    session["role"] = role

    return jsonify({
        "authenticated": True,
        "user_id": f"USR-{abs(hash(email)) % 10000}",
        "email": email,
        "role": role
    }), 200


@app.route("/api/v1/donors/profile", methods=["GET", "POST"])
def api_donor_profile():
    # REQ-F-002 / AC 2: Donor profile & availability management
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        blood_type = data.get("blood_type", "O-")
        location = data.get("location", "San Francisco, CA")
        available = data.get("available", True)

        username = session.get("username", "johndoe")
        target_donor = next((d for d in donors if d["username"] == username), None)
        if not target_donor:
            target_donor = {
                "name": "John Doe",
                "username": username,
                "age": 34,
                "gender": "Male",
                "blood_group": blood_type,
                "location": location,
                "available": available,
                "last_donation": "2025-08-20",
                "donation_count": 2
            }
            donors.append(target_donor)
        else:
            target_donor["blood_group"] = blood_type
            target_donor["location"] = location
            target_donor["available"] = available

        audit_logs.append({
            "action": "DONOR PROFILE UPDATED",
            "details": f"Updated profile for {username}: blood={blood_type}, loc={location}, avail={available}.",
            "user": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        return jsonify({
            "status": "updated",
            "donor": {
                "name": target_donor.get("name", "John Doe"),
                "blood_type": blood_type,
                "location": location,
                "available": available
            }
        }), 200

    username = session.get("username", "johndoe")
    target_donor = next((d for d in donors if d["username"] == username), donors[0] if donors else {})
    return jsonify({
        "id": 1,
        "name": target_donor.get("name", "John Doe"),
        "email": f"{target_donor.get('username', 'johndoe')}@example.com",
        "blood_type": target_donor.get("blood_group", "O-"),
        "location": target_donor.get("location", "San Francisco, CA"),
        "available": target_donor.get("available", True),
        "last_donation_date": target_donor.get("last_donation", "2025-08-20")
    }), 200


@app.route("/api/v1/donors/search", methods=["GET"])
def api_donors_search():
    # REQ-F-003: Recipients search for donors based on blood type & location
    blood_type = request.args.get("blood_type")
    location = request.args.get("location")

    matching = []
    for d in donors:
        if blood_type and blood_type != "Any" and d.get("blood_group") != blood_type:
            continue
        if location and location.lower() not in d.get("location", "").lower():
            continue
        matching.append({
            "id": len(matching) + 1,
            "name": d.get("name"),
            "blood_type": d.get("blood_group"),
            "general_location": d.get("location", "San Francisco, CA"),
            "available": d.get("available", True)
        })

    return jsonify({
        "count": len(matching),
        "donors": matching
    }), 200


@app.route("/api/v1/donors/hotspots", methods=["GET"])
def api_donors_hotspots():
    # REQ-F-004 / AC 3: Clustered hotspots with coarse centroids without revealing exact addresses
    clusters = [
        {
            "district": "Downtown San Francisco",
            "latitude": round(37.7749, 2),
            "longitude": round(-122.4194, 2),
            "donor_count": 14,
            "blood_types": ["O-", "A+", "B+"]
        },
        {
            "district": "East Bay Metro",
            "latitude": round(37.8044, 2),
            "longitude": round(-122.2712, 2),
            "donor_count": 8,
            "blood_types": ["A+", "AB+", "O-"]
        },
        {
            "district": "Silicon Valley South",
            "latitude": round(37.3382, 2),
            "longitude": round(-121.8863, 2),
            "donor_count": 12,
            "blood_types": ["B+", "O-", "A+"]
        }
    ]
    return jsonify({"hotspots": clusters}), 200


@app.route("/api/v1/requests", methods=["GET", "POST"])
def api_requests():
    # REQ-F-005: Recipients submit connection request attaching medical necessity document
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        req_id = f"REQ-{len(connection_requests) + 10235}"
        new_req = {
            "request_id": req_id,
            "recipient_id": data.get("recipient_id", "REC-9876"),
            "blood_type": data.get("blood_type", "O-"),
            "location": data.get("location", "San Francisco, CA"),
            "message": data.get("message", ""),
            "document_name": data.get("document_name", "hospital_letter.pdf"),
            "document_base64": data.get("document_base64", ""),
            "status": "Pending",
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hours_pending": 0.0,
            "reminder_active": False,
            "verified_by": None,
            "verified_at": None,
            "notes": ""
        }
        connection_requests.insert(0, new_req)

        # Secure app notification (REQ-F-007)
        app_notifications.append({
            "id": len(app_notifications) + 1,
            "user_id": new_req["recipient_id"],
            "title": "Request Submitted",
            "message": f"Your connection request {req_id} has been submitted for administrator review.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "read": False
        })

        audit_logs.append({
            "action": "CONNECTION REQUEST CREATED",
            "details": (
                f"Connection request {req_id} ({new_req['blood_type']}) "
                f"created with document {new_req['document_name']}."
            ),
            "user": new_req["recipient_id"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        return jsonify({
            "request_id": req_id,
            "status": "Pending",
            "submitted_at": new_req["submitted_at"],
            "message": "Request submitted for administrator review"
        }), 201

    return jsonify({"requests": connection_requests}), 200


@app.route("/api/v1/requests/<req_id>", methods=["GET"])
def api_request_details(req_id):
    req_item = next((r for r in connection_requests if r["request_id"] == req_id), None)
    if not req_item:
        return jsonify({"error": "Request not found"}), 404
    return jsonify(req_item), 200


@app.route("/api/v1/admin/requests/<req_id>/verify", methods=["POST"])
def api_admin_verify(req_id):
    # REQ-F-006 / AC 4: District Admin review and approve/reject connection request
    data = request.get_json(silent=True) or {}
    action = data.get("action", "Approve").capitalize()
    notes = data.get("notes", "")

    req_item = next((r for r in connection_requests if r["request_id"] == req_id), None)
    if not req_item:
        return jsonify({"error": "Request not found"}), 404

    status = "Approved" if action == "Approve" else "Rejected"
    req_item["status"] = status
    req_item["verified_by"] = session.get("username", "admin_district")
    req_item["verified_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    req_item["notes"] = notes
    req_item["reminder_active"] = False

    # REQ-F-007: Secure app notification
    app_notifications.append({
        "id": len(app_notifications) + 1,
        "user_id": req_item["recipient_id"],
        "title": f"Request {status}",
        "message": f"Your request {req_id} has been {status.lower()} by the District Administrator.",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read": False
    })

    audit_logs.append({
        "action": f"REQUEST {status.upper()}",
        "details": f"District Admin verified request {req_id}: {status}. Notes: {notes}",
        "user": req_item["verified_by"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "request_id": req_id,
        "status": status,
        "verified_by": req_item["verified_by"],
        "verified_at": req_item["verified_at"],
        "notification_sent": True
    }), 200


@app.route("/api/v1/admin/requests/pending", methods=["GET"])
def api_admin_pending_requests():
    # REQ-F-008: Automated reminders for pending requests older than REMINDER_THRESHOLD_HOURS
    pending = [r for r in connection_requests if r["status"] == "Pending"]
    reminders = 0
    for r in pending:
        if r.get("hours_pending", 0) >= REMINDER_THRESHOLD_HOURS:
            r["reminder_active"] = True
            reminders += 1

    return jsonify({
        "pending_count": len(pending),
        "reminders_count": reminders,
        "requests": pending
    }), 200


@app.route("/api/v1/notifications", methods=["GET"])
def api_notifications():
    # REQ-F-007: Secure app notifications
    return jsonify({"notifications": app_notifications}), 200


# -------------------------------------------------------------
# Legacy BDCN Application Routes (Preserved for 100% Backward Compatibility)
# -------------------------------------------------------------
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
    app.run(host=HOST, port=PORT, debug=True)
