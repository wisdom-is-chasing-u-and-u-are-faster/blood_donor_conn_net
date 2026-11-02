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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

# -------------------------------------------------------------
# ARCH-6803 New REST APIs & BDCN Variant A Endpoints
# -------------------------------------------------------------

# Verification records storage
verifications = [
    {
        "id": "1",
        "recipient_name": "Jane Doe",
        "hospital_name": "St. Jude Memorial",
        "physician_name": "Dr. Emily Watson",
        "document_type": "Physician Request",
        "document_name": "physician_request_jane_doe.pdf",
        "status": "pending",
        "submitted_at": "2026-11-02 10:15:00"
    }
]

# Secure messages storage
messages_store = [
    {
        "id": "1",
        "sender": "System",
        "recipient": "all",
        "content": "Welcome to the Blood Donor Connection Network.",
        "timestamp": "2026-11-02 09:00:00"
    }
]

# Verified recipients tracker
verified_recipients = set()


@app.route("/health", methods=["GET"])
def health_probe():
    """Container readiness and liveness probe."""
    return jsonify({"status": "healthy"}), 200


@app.route("/api/v1/auth/social", methods=["POST"])
def api_social_login():
    """REQ-F-007: Support user login via Google, Apple, and Facebook OAuth."""
    data = request.get_json() or {}
    provider = data.get("provider", "google").lower()
    username = data.get("username", f"user_{provider}")
    role = data.get("role", "donor")

    if provider not in ["google", "apple", "facebook"]:
        return jsonify({"error": "Unsupported provider. Must be google, apple, or facebook."}), 400

    session["username"] = username
    session["role"] = role

    audit_logs.append({
        "action": "API SOCIAL LOGIN",
        "details": f"User {username} authenticated via {provider.capitalize()} with role {role}.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "success": True,
        "username": username,
        "role": role,
        "message": f"Successfully authenticated via {provider.capitalize()}"
    }), 200


@app.route("/api/v1/verifications/upload", methods=["POST"])
def api_upload_verification():
    """REQ-F-003, REQ-F-014: Digital upload of documents for recipient verification."""
    data = request.get_json() or {}
    recipient_name = data.get("recipient_name") or session.get("username", "Anonymous Recipient")
    hospital_name = data.get("hospital_name", "General Hospital")
    physician_name = data.get("physician_name", "Attending Physician")
    document_type = data.get("document_type", "Hospital Letter")
    document_name = data.get("document_name", "verification_doc.pdf")

    verif_id = str(len(verifications) + 1)
    record = {
        "id": verif_id,
        "recipient_name": recipient_name,
        "hospital_name": hospital_name,
        "physician_name": physician_name,
        "document_type": document_type,
        "document_name": document_name,
        "status": "pending",
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    verifications.append(record)

    audit_logs.append({
        "action": "VERIFICATION DOCUMENT UPLOAD",
        "details": f"Uploaded {document_type} ({document_name}) for recipient {recipient_name}.",
        "user": session.get("username", recipient_name),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "verification_id": verif_id,
        "status": "pending",
        "message": "Document uploaded and submitted for administrator verification."
    }), 201


@app.route("/api/v1/admin/verifications", methods=["GET"])
def api_admin_verifications():
    """List verification queue records for administrators."""
    return jsonify({"verifications": verifications}), 200


@app.route("/api/v1/admin/verifications/<id>/action", methods=["POST"])
def api_admin_verification_action(id):
    """REQ-F-013: District admin approve/reject pending recipient verification."""
    data = request.get_json() or {}
    action = data.get("action", "").lower()
    notes = data.get("notes", "")

    target = next((v for v in verifications if v["id"] == str(id)), None)
    if not target:
        return jsonify({"error": "Verification record not found"}), 404

    if action not in ["approve", "reject"]:
        return jsonify({"error": "Invalid action. Must be 'approve' or 'reject'."}), 400

    target["status"] = "approved" if action == "approve" else "rejected"
    if action == "approve":
        verified_recipients.add(target["recipient_name"])

    audit_logs.append({
        "action": f"RECIPIENT VERIFICATION {action.upper()}",
        "details": f"{action.capitalize()} verification #{id} for {target['recipient_name']}. Notes: {notes}",
        "user": session.get("username", "District Admin"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({
        "id": str(id),
        "status": target["status"],
        "message": f"Verification successfully {target['status']}."
    }), 200


@app.route("/api/v1/donors/hotspots", methods=["GET"])
def api_donor_hotspots():
    """REQ-F-005, REQ-F-011: Donor hotspot density clustering with coarse coordinates, locked for unverified recipients."""
    username = session.get("username", "")
    role = session.get("role", "")

    # AC: Unverified recipient cannot view or access unlocked map details
    if role == "recipient" and username not in verified_recipients:
        return jsonify({
            "error": "Access restricted. Recipient must be verified by district admin to view donor hotspots.",
            "verified": False,
            "hotspots": []
        }), 403

    # Coarse centroid clustering obfuscation (rounded coordinates, no exact residential addresses)
    hotspots = [
        {
            "cluster_id": "cluster_north",
            "city": "Springfield",
            "district": "District North",
            "lat": 39.78,
            "lng": -89.65,
            "donor_count": 14,
            "blood_types": ["O+", "A+", "B+"]
        },
        {
            "cluster_id": "cluster_metro",
            "city": "Metropolis",
            "district": "Downtown Metro",
            "lat": 37.15,
            "lng": -88.73,
            "donor_count": 22,
            "blood_types": ["O-", "AB+", "B-"]
        },
        {
            "cluster_id": "cluster_east",
            "city": "Gotham",
            "district": "Gotham Harbor",
            "lat": 40.71,
            "lng": -74.00,
            "donor_count": 8,
            "blood_types": ["A-", "O+", "AB-"]
        }
    ]
    return jsonify({"hotspots": hotspots, "verified": True}), 200


@app.route("/api/v1/messages", methods=["GET"])
def api_get_messages():
    """Fetch secure in-system notification messages."""
    return jsonify({"messages": messages_store}), 200


@app.route("/api/v1/messages/send", methods=["POST"])
def api_send_message():
    """REQ-F-012, REQ-F-013: Contact initiation locked until recipient approved."""
    username = session.get("username", "anonymous")
    role = session.get("role", "")

    # Lock contact initiation if unverified recipient
    if role == "recipient" and username not in verified_recipients:
        return jsonify({
            "error": "Contact initiation is locked until your recipient profile is verified by an administrator."
        }), 403

    data = request.get_json() or {}
    recipient = data.get("recipient", "all")
    content = data.get("content", "")

    if not content:
        return jsonify({"error": "Message content cannot be empty."}), 400

    msg_id = str(len(messages_store) + 1)
    msg = {
        "id": msg_id,
        "sender": username,
        "recipient": recipient,
        "content": content,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    messages_store.append(msg)

    return jsonify({
        "success": True,
        "message_id": msg_id,
        "message": "Secure message sent successfully."
    }), 201


@app.route("/api/v1/achievements/share", methods=["POST"])
def api_share_achievement():
    """REQ-F-009: API for social sharing of badges and milestones."""
    data = request.get_json() or {}
    badge_id = data.get("badge_id", "hero_tier")
    platform = data.get("platform", "twitter").lower()

    share_url = f"https://{platform}.com/intent/tweet?text=Proud%20to%20be%20a%20Blood%20Donor%20Hero%20on%20BDCN!"
    return jsonify({
        "badge_id": badge_id,
        "platform": platform,
        "share_url": share_url,
        "status": "shared"
    }), 200


@app.route("/pages/<page_name>")
def render_page(page_name):
    """Render Variant A self-contained UI pages."""
    if not page_name.endswith(".html"):
        page_name += ".html"
    return render_template(f"pages/{page_name}")


