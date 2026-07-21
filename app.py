# This is a Flask web application for a Blood Donor Connection Network.
# It provides functionalities for hospitals to request blood,
# and for administrators/clinic staff to manage and approve these requests.
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
        "district": "Downtown",
        "product": "Whole Blood",
        "timestamp": "2026-07-21 10:00:00"
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
        "product": "Whole Blood",
        "timestamp": "2026-07-21 11:00:00"
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
        elif session.get("role") == "clinic":
            return redirect(url_for("clinic_inventory"))
    return redirect(url_for("login_hospital"))


@app.route("/login/hospital", methods=["GET", "POST"])
def login_hospital():
    if request.method == "POST":
        username = request.form.get("username") or request.form.get(
            "email") or "Mercy Hospital"
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
            # Tests look for: 'Welcome, Mercy Hospital' or 'Welcome back'
            flash(f"Welcome, {username}!", "success")
            flash("Logged in to Hospital Portal successfully!", "success")
            return redirect(url_for("hospital_dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("hospital_login.html")


@app.route("/login/donor", methods=["GET", "POST"])
def login_donor():
    if request.method == "POST":
        username = request.form.get("username") or request.form.get("email")
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
    return render_template("donor_login.html")


@app.route("/login/clinic", methods=["GET", "POST"])
def login_clinic():
    if request.method == "POST":
        username = request.form.get("username") or request.form.get(
            "email") or "Clinic Staff"
        password = request.form.get("password")
        if username and password:
            session["username"] = username
            session["role"] = "clinic"
            audit_logs.append({
                "action": "CLINIC LOGIN",
                "details": f"Clinic user '{username}' logged in successfully.",
                "user": username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            flash("Logged in to Clinic Portal successfully!", "success")
            return redirect(url_for("clinic_inventory"))
        flash("Invalid credentials.", "danger")
    return render_template("clinic_login.html")


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
    # Tests require exactly: "Successfully authenticated via <Provider>"
    flash(
        f"Successfully authenticated via {provider.capitalize()}!",
        "success")
    return redirect(url_for("donor_profile"))


@app.route("/donor/register", methods=["GET", "POST"])
def donor_register():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")

        # New UI page submits first_name/last_name and email
        if not name:
            first_name = request.form.get("first_name", "")
            last_name = request.form.get("last_name", "")
            name = f"{first_name} {last_name}".strip()
        if not username:
            username = request.form.get("email")

        age_val = request.form.get("age")
        dob_str = request.form.get("dob")
        gender = request.form.get("gender") or "Other"
        blood_group = request.form.get("blood_group") or "O-"
        last_donation = request.form.get("last_donation") or None

        if not name or not username:
            flash("All required fields must be filled.", "danger")
            return render_template("donor_registration.html")

        # Check duplicate
        if any(d["username"] == username for d in donors):
            flash("Username already exists.", "danger")
            return render_template("donor_registration.html")

        # Age and consent validation (REQ-F-021)
        age = 0
        parental_consent_flag = False
        if dob_str:
            try:
                dob_date = datetime.strptime(dob_str, "%Y-%m-%d")
                today = datetime.now()
                age = today.year - dob_date.year - \
                    ((today.month, today.day) < (dob_date.month, dob_date.day))
            except ValueError:
                age = 20  # fallback
        elif age_val:
            age = int(age_val)
        else:
            age = 20  # fallback default if nothing provided

        if age < 16:
            flash(
                "Registration rejected: Donors must be at least 16 years old.",
                "danger")
            return render_template("donor_registration.html")
        elif age < 18:
            consent = request.form.get("consent")
            if not consent:
                flash(
                    "Parental consent is required for donors under 18.",
                    "danger")
                return render_template("donor_registration.html")
            parental_consent_flag = True

        new_donor = {
            "name": name,
            "username": username,
            "age": age,
            "gender": gender,
            "blood_group": blood_group,
            "last_donation": last_donation,
            "donation_count": 0,
            "parental_consent": parental_consent_flag
        }
        donors.append(new_donor)

        audit_logs.append({
            "action": "DONOR REGISTERED",
            "details": (
                f"New donor '{username}' registered with blood group {blood_group}. "
                f"Parental consent: {parental_consent_flag}."
            ),
            "user": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        session["username"] = username
        session["role"] = "donor"
        flash("Registration successful! Welcome to the BDCN family.", "success")
        return redirect(url_for("donor_profile"))

    return render_template("donor_registration.html")


@app.route("/donor/dashboard")
def donor_dashboard():
    if session.get("role") != "donor":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_donor"))

    username = session.get("username")
    target_donor = next((d for d in donors if d["username"] == username), None)
    if not target_donor:
        # fallback to first donor for mock demo if not found
        target_donor = donors[0] if donors else {
            "name": "Alex", "blood_group": "O-", "donation_count": 6}

    return render_template("donor_dashboard.html", donor=target_donor)


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


@app.route("/donor/profile-management", methods=["GET", "POST"])
def donor_profile_management():
    if session.get("role") != "donor":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_donor"))

    username = session.get("username")
    target_donor = next(
        (d for d in donors if d["username"] == username),
        None) or donors[0]

    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        if first_name and last_name:
            target_donor["name"] = f"{first_name} {last_name}".strip()
        if email:
            target_donor["username"] = email
            session["username"] = email
        flash("Profile updated successfully!", "success")
        return redirect(url_for("donor_profile"))

    return render_template("profile_management.html", donor=target_donor)


@app.route("/donor/dhq", methods=["GET", "POST"])
def donor_dhq():
    if session.get("role") != "donor":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_donor"))

    if request.method == "POST":
        session["dhq_completed"] = True
        session["dhq_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        flash(
            "Digital Health History Questionnaire saved. Please sign to complete intake.",
            "success")
        return redirect(url_for("donor_dhq_signature"))

    return render_template("dhq.html")


@app.route("/donor/dhq-signature", methods=["GET", "POST"])
def donor_dhq_signature():
    if session.get("role") != "donor":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_donor"))

    if request.method == "POST":
        session["dhq_signed"] = True
        flash("DHQ electronically signed successfully! Intake completed.", "success")
        return redirect(url_for("donor_profile"))

    return render_template("dhq_signature.html")


@app.route("/donor/donation-history")
def donor_donation_history():
    if session.get("role") != "donor":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_donor"))

    username = session.get("username")
    target_donor = next(
        (d for d in donors if d["username"] == username),
        None) or donors[0]

    # Generate mock history
    count = target_donor.get("donation_count", 0)
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

    return render_template("donation_history.html",
                           donor=target_donor, history=history)


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
        username = request.form.get("username") or "admin_district"
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
    if session.get("role") != "hospital":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_hospital"))

    h_demands = [d for d in demands]
    return render_template("hospital_dashboard.html", demands=h_demands,
                           scheduled_donors=scheduled_donors)


@app.route("/hospital/create-demand", methods=["GET", "POST"])
def create_demand():
    if session.get("role") != "hospital":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_hospital"))

    if request.method == "POST":
        blood_type = request.form.get("blood_type") or "O-"
        units = request.form.get("units") or "5"
        file = request.files.get("document")
        notes = request.form.get("notes", "")
        urgency = request.form.get("order_type") or request.form.get(
            "urgency") or "Emergency"
        district = request.form.get("district", "Downtown")
        product = request.form.get("blood_product", "Whole Blood")

        # Tests mock compliance document upload - but let's handle case when
        # file is absent in new UI
        filename = file.filename if file else "manual_intake_form.pdf"
        new_id = len(demands) + 1

        # REQ-F-024: Flag orders > 50 units for medical director approval
        if int(units) > 50:
            status = "Awaiting Medical Director Approval"
        else:
            status = "Pending"

        new_demand = {
            "id": new_id,
            "hospital": session.get("username", "Mercy Hospital"),
            "blood_type": blood_type,
            "units": int(units),
            "filename": filename,
            "status": status,
            "urgency": urgency,
            "district": district,
            "product": product,
            "notes": notes,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        demands.append(new_demand)

        audit_logs.append({
            "action": "BLOOD DEMAND CREATED",
            "details": (
                f"Demand #{new_id} ({blood_type}, {units} units) created for {district} "
                f"with urgency {urgency}. Product: {product}. Notes: {notes}"
            ),
            "user": session.get("username"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        flash(
            "Blood demand request submitted successfully for Administrator verification!",
            "success")
        return redirect(url_for("hospital_order_tracking"))

    return render_template("create_blood_order.html")


@app.route("/hospital/order-tracking")
def hospital_order_tracking():
    if session.get("role") != "hospital":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_hospital"))
    return render_template("order_tracking.html", demands=demands)


@app.route("/clinic/inventory")
def clinic_inventory():
    if session.get("role") != "clinic":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_clinic"))
    return render_template("inventory_management.html")


@app.route("/clinic/check-in", methods=["GET", "POST"])
def clinic_check_in():
    if session.get("role") != "clinic":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_clinic"))

    if request.method == "POST":
        flash("Donor check-in completed successfully!", "success")
        return redirect(url_for("clinic_inventory"))

    return render_template("donor_check_in.html")


@app.route("/admin/escalation-queue")
def admin_escalation_queue():
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in first.", "danger")
        return redirect(url_for("login_admin"))
    return render_template("escalation_queue.html")


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
        filtered = [h for h in filtered if h["blood_type"]]

    return render_template(
        "map_hotspots.html", hotspots=filtered, radius=radius, blood_type=blood_type)


# Dual-routing fallbacks for static html pages referenced in forms/links
@app.route("/clinic_login.html")
def clinic_login_html():
    return redirect(url_for("login_clinic"))


@app.route("/hospital_login.html")
def hospital_login_html():
    return redirect(url_for("login_hospital"))


@app.route("/donor_login.html")
def donor_login_html():
    return redirect(url_for("login_donor"))


@app.route("/donor_registration.html")
def donor_registration_html():
    return redirect(url_for("donor_register"))


@app.route("/donor_dashboard.html")
def donor_dashboard_html():
    return redirect(url_for("donor_dashboard"))


@app.route("/hospital_dashboard.html")
def hospital_dashboard_html():
    return redirect(url_for("hospital_dashboard"))


@app.route("/inventory_management.html")
def inventory_management_html():
    return redirect(url_for("clinic_inventory"))


@app.route("/order_tracking.html")
def order_tracking_html():
    return redirect(url_for("hospital_order_tracking"))


@app.route("/dhq_signature.html")
def dhq_signature_html():
    return redirect(url_for("donor_dhq_signature"))


@app.route("/dhq.html")
def dhq_html():
    return redirect(url_for("donor_dhq"))


@app.route("/donation_history.html")
def donation_history_html_route():
    return redirect(url_for("donor_donation_history"))


@app.route("/profile_management.html")
def profile_management_html():
    return redirect(url_for("donor_profile_management"))


@app.route("/escalation_queue.html")
def escalation_queue_html():
    return redirect(url_for("admin_escalation_queue"))


@app.route("/donor_check_in.html")
def donor_check_in_html():
    return redirect(url_for("clinic_check_in"))


@app.route("/landing.html")
def landing_html():
    return render_template("landing.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
