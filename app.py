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


# Added Inventory Data Structure & Appointments for ARCH-150
inventory = [
    {
        "id": 1,
        "facility": "Central Regional Blood Bank",
        "blood_type": "A+",
        "units": 25,
        "component": "Whole Blood",
        "expiration_date": "2026-08-08",
        "days_to_expiration": 4,
        "is_near_expiration": True,
        "status": "EXPIRING_SOON"
    },
    {
        "id": 2,
        "facility": "North District Facility",
        "blood_type": "O-",
        "units": 8,
        "component": "Red Blood Cells",
        "expiration_date": "2026-08-05",
        "days_to_expiration": 1,
        "is_near_expiration": True,
        "status": "EXPIRING_SOON"
    },
    {
        "id": 3,
        "facility": "East Valley Hub",
        "blood_type": "B+",
        "units": 40,
        "component": "Platelets",
        "expiration_date": "2026-08-30",
        "days_to_expiration": 26,
        "is_near_expiration": False,
        "status": "AVAILABLE"
    },
    {
        "id": 4,
        "facility": "South Coast Center",
        "blood_type": "AB-",
        "units": 12,
        "component": "Plasma",
        "expiration_date": "2026-08-07",
        "days_to_expiration": 3,
        "is_near_expiration": True,
        "status": "EXPIRING_SOON"
    }
]

donor_appointments = [
    {
        "id": 1,
        "donor_username": "johndoe",
        "center": "Downtown Donation Center",
        "date": "2026-08-15",
        "time": "10:30 AM",
        "blood_type": "A+",
        "status": "CONFIRMED"
    },
    {
        "id": 2,
        "donor_username": "janesmith",
        "center": "North District Clinic",
        "date": "2026-08-18",
        "time": "02:15 PM",
        "blood_type": "O-",
        "status": "CONFIRMED"
    }
]


@app.route("/login")
def login_redirect():
    return redirect(url_for("login_donor"))


@app.route("/register")
def register_redirect():
    return redirect(url_for("donor_register"))


@app.route("/donor/dashboard")
def donor_dashboard():
    if session.get("role") != "donor":
        flash("Unauthorized. Please log in as a donor.", "danger")
        return redirect(url_for("login_donor"))

    username = session.get("username")
    target_donor = next((d for d in donors if d["username"] == username), None)
    if not target_donor:
        flash("Donor profile not found.", "danger")
        return redirect(url_for("logout"))

    my_appointments = [a for a in donor_appointments if a.get("donor_username") == username]

    # Eligibility calculation
    eligibility_status = "Eligible to donate now!"
    days_until_eligible = 0
    if target_donor.get("last_donation"):
        try:
            last_date = datetime.strptime(target_donor["last_donation"], "%Y-%m-%d")
            delta = (datetime.now() - last_date).days
            if delta < 56:
                days_until_eligible = 56 - delta
                eligibility_status = f"You are eligible to donate in {days_until_eligible} days."
        except Exception:
            pass

    return render_template("03_donor_dashboard.html",
                           donor=target_donor,
                           eligibility_status=eligibility_status,
                           days_until_eligible=days_until_eligible,
                           appointments=my_appointments)


@app.route("/donor/appointments", methods=["GET", "POST"])
@app.route("/donor/book-appointment", methods=["GET", "POST"])
def donor_appointments_route():
    if session.get("role") != "donor":
        flash("Unauthorized. Please log in as a donor.", "danger")
        return redirect(url_for("login_donor"))

    username = session.get("username")
    target_donor = next((d for d in donors if d["username"] == username), None)

    if request.method == "POST":
        center = request.form.get("center") or request.form.get("facility") or "Central Donation Clinic"
        date = request.form.get("date") or "2026-08-20"
        time = request.form.get("time") or "10:00 AM"
        blood_type = request.form.get("blood_type") or (target_donor["blood_group"] if target_donor else "O+")

        new_appt = {
            "id": len(donor_appointments) + 1,
            "donor_username": username,
            "center": center,
            "date": date,
            "time": time,
            "blood_type": blood_type,
            "status": "CONFIRMED"
        }
        donor_appointments.append(new_appt)
        scheduled_donors.append(
            {
                "name": target_donor["name"] if target_donor else username,
                "blood_type": blood_type,
                "time": f"{date} {time}"
            })

        audit_logs.append({
            "action": "APPOINTMENT BOOKED",
            "details": f"Booked appointment at {center} on {date} at {time}.",
            "user": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        flash("Appointment scheduled successfully!", "success")
        return redirect(url_for("donor_dashboard"))

    my_appointments = [a for a in donor_appointments if a.get("donor_username") == username]
    return render_template("04_donor_appointments.html", donor=target_donor, appointments=my_appointments)


@app.route("/admin/dashboard")
@app.route("/inventory/dashboard")
def admin_inventory_dashboard():
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in as administrator.", "danger")
        return redirect(url_for("login_admin"))

    near_expiration_units = [item for item in inventory if item.get(
        "is_near_expiration") or item.get("days_to_expiration", 99) <= 7]
    total_units = sum(item["units"] for item in inventory)

    return render_template("08_admin_dashboard.html",
                           inventory=inventory,
                           near_expiration_units=near_expiration_units,
                           total_units=total_units,
                           pending_demands=[d for d in demands if d.get("status") == "Pending"])


@app.route("/inventory/manual-entry", methods=["GET", "POST"])
@app.route("/admin/inventory/manual-entry", methods=["GET", "POST"])
def inventory_manual_entry():
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in as administrator.", "danger")
        return redirect(url_for("login_admin"))

    if request.method == "POST":
        facility = request.form.get("facility") or "Central Blood Bank"
        blood_type = request.form.get("blood_type")
        units = request.form.get("units")
        component = request.form.get("component") or "Whole Blood"
        expiration_date = request.form.get("expiration_date") or "2026-09-01"

        if not blood_type or not units:
            flash("Blood type and units are required.", "danger")
            return redirect(url_for("inventory_manual_entry"))

        units_int = int(units)
        days_exp = 30
        try:
            exp_dt = datetime.strptime(expiration_date, "%Y-%m-%d")
            days_exp = (exp_dt - datetime.now()).days
        except Exception:
            pass

        is_near = days_exp <= 7
        new_item = {
            "id": len(inventory) + 1,
            "facility": facility,
            "blood_type": blood_type,
            "units": units_int,
            "component": component,
            "expiration_date": expiration_date,
            "days_to_expiration": days_exp,
            "is_near_expiration": is_near,
            "status": "EXPIRING_SOON" if is_near else "AVAILABLE"
        }
        inventory.append(new_item)

        audit_logs.append({
            "action": "INVENTORY MANUAL ENTRY",
            "details": f"Added {units_int} units of {blood_type} ({component}) at {facility}.",
            "user": session.get("username"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        flash(f"Successfully added {units_int} units of {blood_type} to inventory!", "success")
        return redirect(url_for("admin_inventory_dashboard"))

    return render_template("05_inventory_manual_entry.html")


@app.route("/inventory/csv-upload", methods=["GET", "POST"])
@app.route("/admin/inventory/csv-upload", methods=["GET", "POST"])
def inventory_csv_upload():
    if session.get("role") != "admin":
        flash("Unauthorized. Please log in as administrator.", "danger")
        return redirect(url_for("login_admin"))

    if request.method == "POST":
        file = request.files.get("csv_file") or request.files.get("file")
        if not file:
            flash("Please select a CSV file to upload.", "danger")
            return redirect(url_for("inventory_csv_upload"))

        content = file.stream.read().decode("utf-8")
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        added_count = 0

        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) >= 3:
                facility = parts[0].strip() if len(parts) > 0 else "Main Facility"
                blood_type = parts[1].strip() if len(parts) > 1 else "O+"
                units = int(parts[2].strip()) if parts[2].strip().isdigit() else 5
                component = parts[3].strip() if len(parts) > 3 else "Whole Blood"
                exp_date = parts[4].strip() if len(parts) > 4 else "2026-08-30"

                days_exp = 20
                try:
                    exp_dt = datetime.strptime(exp_date, "%Y-%m-%d")
                    days_exp = (exp_dt - datetime.now()).days
                except Exception:
                    pass

                is_near = days_exp <= 7
                inventory.append({
                    "id": len(inventory) + 1,
                    "facility": facility,
                    "blood_type": blood_type,
                    "units": units,
                    "component": component,
                    "expiration_date": exp_date,
                    "days_to_expiration": days_exp,
                    "is_near_expiration": is_near,
                    "status": "EXPIRING_SOON" if is_near else "AVAILABLE"
                })
                added_count += 1

        audit_logs.append({
            "action": "INVENTORY CSV UPLOAD",
            "details": f"Uploaded CSV '{file.filename}' - ingested {added_count} inventory items.",
            "user": session.get("username"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        flash(f"CSV ingestion complete: {added_count} inventory records added successfully!", "success")
        return redirect(url_for("admin_inventory_dashboard"))

    return render_template("06_inventory_csv_upload.html")


@app.route("/critical-code-red", methods=["GET", "POST"])
@app.route("/hospital/critical-code-red", methods=["GET", "POST"])
def critical_code_red():
    if session.get("role") != "hospital" and session.get("role") != "admin":
        flash("Unauthorized. Hospital staff login required.", "danger")
        return redirect(url_for("login_hospital"))

    if request.method == "POST":
        hospital = request.form.get("hospital_name") or session.get("username") or "City Emergency Hospital"
        blood_type = request.form.get("blood_type") or "O-"
        units = request.form.get("units") or "10"
        district = request.form.get("district") or "Central District"

        units_int = int(units)
        new_id = len(demands) + 1
        new_demand = {
            "id": new_id,
            "hospital": hospital,
            "blood_type": blood_type,
            "units": units_int,
            "filename": "code_red_emergency.pdf",
            "status": "Approved",
            "urgency": "CRITICAL_CODE_RED",
            "district": district
        }
        demands.append(new_demand)

        alert_id = len(alerts) + 1
        alerts.append({
            "id": alert_id,
            "hospital": hospital,
            "blood_type": blood_type,
            "status": "CRITICAL_CODE_RED_ACTIVE"
        })

        audit_logs.append({
            "action": "CRITICAL CODE RED SUBMITTED",
            "details": f"CODE RED #{new_id} ({blood_type}) submitted by {hospital} in {district}.",
            "user": session.get("username"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        flash(
            f"CRITICAL CODE RED alert dispatched! {units_int} units requested.", "danger")
        return redirect(url_for("hospital_dashboard"))

    return render_template("07_critical_code_red.html")
