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
        "demand_id": 1,
        "hospital": "General Hospital",
        "blood_type": "A+",
        "status": "Active",
        "urgency": "Emergency",
        "district": "Downtown"
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

# Failed OCR Documents Queue (REQ-F-012/REQ-F-015/REQ-F-016)
ocr_documents = [
    {
        "id": 1,
        "donor_name": "Alice Johnson",
        "filename": "medical_clearance_alice.jpg",
        "reason": "OCR error parsing handwritten physical clearance date.",
        "status": "Pending",
        "escalated": False,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 2,
        "donor_name": "Bob Miller",
        "filename": "bob_eligibility_report.pdf",
        "reason": "Missing physician signature block in OCR bounding box check.",
        "status": "Pending",
        "escalated": False,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
]

# Emergency Override settings (REQ-F-013)
emergency_settings = {
    "national_override_active": False
}


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

    # Secure anonymized token (REQ-F-009/12)
    donor_token = "f81d4fae-7dec-11d0-a765-00a0c91e" + str(abs(hash(username)) % 10000)

    return render_template("donor_profile.html",
                           donor=target_donor, badges=badges, history=history, donor_token=donor_token)


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
                "demand_id": target_demand["id"],
                "hospital": target_demand["hospital"],
                "blood_type": target_demand["blood_type"],
                "status": "Active",
                "urgency": target_demand.get("urgency", "Emergency"),
                "district": target_demand.get("district", "Downtown")
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


# --- NEW BDCN FRONTEND WORKFLOW ROUTES (ARCH-5227) ---

# 1 · Donor Alerts (REQ-F-007)
@app.route("/donor/alerts")
def donor_alerts():
    if session.get("role") != "donor":
        flash("Unauthorized. Please log in as a donor.", "danger")
        return redirect(url_for("login_donor"))

    username = session.get("username")
    target_donor = next((d for d in donors if d["username"] == username), None)
    if not target_donor:
        flash("Donor profile not found.", "danger")
        return redirect(url_for("login_donor"))

    # Active alert notifications matching the donor's blood type (unless override is active, which might bypass)
    donor_blood = target_donor["blood_group"]
    matching_alerts = []
    for a in alerts:
        # Compatibility matching (e.g. O- is universal donor, compatible blood group, or literal match)
        if a["blood_type"] == donor_blood or donor_blood == "O-":
            matching_alerts.append(a)

    return render_template("donor_alerts.html", alerts=matching_alerts, donor=target_donor)


# 2 · Donor Alert Detail (REQ-F-007)
@app.route("/donor/alert/<int:alert_id>")
def donor_alert_detail(alert_id):
    if session.get("role") != "donor":
        flash("Unauthorized.", "danger")
        return redirect(url_for("login_donor"))

    target_alert = next((a for a in alerts if a["id"] == alert_id), None)
    if not target_alert:
        flash("Alert not found.", "danger")
        return redirect(url_for("donor_alerts"))

    return render_template("donor_alert_detail.html", alert=target_alert)


# 3 · Donor Alert Actions: Accept & Decline (REQ-F-007)
@app.route("/donor/alert/<int:alert_id>/accept", methods=["POST"])
def donor_accept_alert(alert_id):
    if session.get("role") != "donor":
        flash("Unauthorized.", "danger")
        return redirect(url_for("login_donor"))

    target_alert = next((a for a in alerts if a["id"] == alert_id), None)
    username = session.get("username")

    if target_alert:
        target_alert["status"] = "Accepted"

        # Add to audit logs
        audit_logs.append({
            "action": "DONOR ACCEPTED ALERT",
            "details": (
                f"Donor '{username}' accepted alert #{alert_id} "
                f"for {target_alert['blood_type']} at {target_alert['hospital']}."
            ),
            "user": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        flash("Thank you! You have accepted the request. Please follow the travel route below.", "success")
        return redirect(url_for("donor_route", alert_id=alert_id))

    flash("Alert not found.", "danger")
    return redirect(url_for("donor_alerts"))


@app.route("/donor/alert/<int:alert_id>/decline", methods=["POST"])
def donor_decline_alert(alert_id):
    if session.get("role") != "donor":
        flash("Unauthorized.", "danger")
        return redirect(url_for("login_donor"))

    target_alert = next((a for a in alerts if a["id"] == alert_id), None)
    username = session.get("username")

    if target_alert:
        target_alert["status"] = "Declined"

        audit_logs.append({
            "action": "DONOR DECLINED ALERT",
            "details": f"Donor '{username}' declined alert #{alert_id} for {target_alert['blood_type']}.",
            "user": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        flash("You have declined the request alert.", "info")
        return redirect(url_for("donor_alerts"))

    flash("Alert not found.", "danger")
    return redirect(url_for("donor_alerts"))


# 4 · Travel Route Map (REQ-F-008 / REQ-F-011)
@app.route("/donor/route/<int:alert_id>")
def donor_route(alert_id):
    if session.get("role") != "donor":
        flash("Unauthorized.", "danger")
        return redirect(url_for("login_donor"))

    target_alert = next((a for a in alerts if a["id"] == alert_id), None)
    if not target_alert:
        flash("Alert not found.", "danger")
        return redirect(url_for("donor_alerts"))

    # Map routing coordinates or details matching design layout
    route_details = {
        "start": "Donor Location (Your District)",
        "destination": f"{target_alert['hospital']} ({target_alert['district']})",
        "distance": "5.4 km",
        "duration": "12 mins",
        "payload_size": "1.2 KB (optimized for 3G connection)"
    }

    return render_template("map_routing.html", alert=target_alert, route=route_details)


# 5 · Admin OCR Manual Review Queue (REQ-F-012/15)
@app.route("/admin/ocr-queue")
def admin_ocr_queue():
    if session.get("role") != "admin":
        flash("Unauthorized.", "danger")
        return redirect(url_for("login_admin"))

    return render_template("ocr_queue.html", documents=ocr_documents, override=emergency_settings)


# 6 · Admin OCR Document Action & Manual Escalation (REQ-F-012/16)
@app.route("/admin/ocr-verify/<int:doc_id>", methods=["POST"])
def admin_ocr_verify(doc_id):
    if session.get("role") != "admin":
        flash("Unauthorized.", "danger")
        return redirect(url_for("login_admin"))

    action = request.form.get("action")
    target_doc = next((d for d in ocr_documents if d["id"] == doc_id), None)
    username = session.get("username")

    if target_doc:
        if action == "approve":
            target_doc["status"] = "Verified"
            audit_logs.append({
                "action": "OCR DOC APPROVED",
                "details": f"OCR Document #{doc_id} for '{target_doc['donor_name']}' approved manually.",
                "user": username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash(f"Successfully verified document for {target_doc['donor_name']}.", "success")
        elif action == "reject":
            target_doc["status"] = "Rejected"
            audit_logs.append({
                "action": "OCR DOC REJECTED",
                "details": f"OCR Document #{doc_id} for '{target_doc['donor_name']}' rejected manually.",
                "user": username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash(f"Rejected document for {target_doc['donor_name']}.", "warning")
        elif action == "escalate":
            target_doc["escalated"] = True
            audit_logs.append({
                "action": "OCR DOC ESCALATED",
                "details": (
                    f"OCR Document #{doc_id} manually escalated to "
                    f"regional supervisor (escalation threshold exceeded)."
                ),
                "user": username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash(f"Document #{doc_id} has been escalated to regional supervisor.", "danger")
        return redirect(url_for("admin_ocr_queue"))

    flash("Document not found.", "danger")
    return redirect(url_for("admin_ocr_queue"))


# 7 · Toggle National Emergency Override (REQ-F-013)
@app.route("/admin/toggle-override", methods=["POST"])
def toggle_emergency_override():
    if session.get("role") != "admin":
        flash("Unauthorized.", "danger")
        return redirect(url_for("login_admin"))

    username = session.get("username")
    active = request.form.get("override") == "true"
    emergency_settings["national_override_active"] = active

    audit_logs.append({
        "action": "EMERGENCY OVERRIDE TOGGLED",
        "details": f"National Emergency Override setting changed to: {active}.",
        "user": username,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    if active:
        flash("National Emergency Override AUTHORIZED. All frequency matching rules bypassed.", "danger")
    else:
        flash("Emergency override disabled. Standard compliance rules restored.", "info")

    return redirect(url_for("admin_ocr_queue"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
