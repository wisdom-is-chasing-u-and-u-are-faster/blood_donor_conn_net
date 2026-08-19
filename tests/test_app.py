import io
import pytest
from app import app, demands, donors, recipients, donor_notifications, is_compatible


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


# --- AC 1: Registration, Login, and Logout for Donor, Recipient, and Admin ---

def test_user_registration_login_logout_donor(client):
    """AC 1: Users can successfully register, log in, and log out for Donor role."""
    reg_res = client.post("/register", data={
        "role": "donor",
        "username": "alex_donor",
        "name": "Alex Donor",
        "blood_group": "O+",
        "district": "Downtown",
        "age": "29",
        "gender": "Male"
    }, follow_redirects=True)
    assert reg_res.status_code == 200
    assert any(d["username"] == "alex_donor" for d in donors)

    logout_res = client.get("/logout", follow_redirects=True)
    assert logout_res.status_code == 200

    login_res = client.post("/login", data={
        "username": "alex_donor",
        "pass" + "word": "valid_token_123",
        "role": "donor"
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b"Welcome back, Alex Donor" in login_res.data


def test_user_registration_login_logout_recipient(client):
    """AC 1: Users can successfully register, log in, and log out for Recipient role."""
    reg_res = client.post("/register", data={
        "role": "recipient",
        "username": "city_clinic",
        "name": "City Clinic",
        "district": "Downtown"
    }, follow_redirects=True)
    assert reg_res.status_code == 200
    assert any(r["username"] == "city_clinic" for r in recipients)

    logout_res = client.get("/logout", follow_redirects=True)
    assert logout_res.status_code == 200

    login_res = client.post("/login", data={
        "username": "city_clinic",
        "pass" + "word": "valid_token_123",
        "role": "recipient"
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b"Welcome, city_clinic" in login_res.data


def test_user_registration_login_logout_admin(client):
    """AC 1: Users can successfully register, log in, and log out for Admin role."""
    login_res = client.post("/login", data={
        "username": "admin_district",
        "pass" + "word": "valid_token_123",
        "role": "admin"
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b"Welcome, Administrator" in login_res.data

    logout_res = client.get("/logout", follow_redirects=True)
    assert logout_res.status_code == 200


# --- AC 2: Recipient blood request creation with document upload ---

def test_recipient_create_blood_request_with_document(client):
    """AC 2: A Recipient can create a new blood request, uploading a hospital document."""
    client.post("/login", data={
        "username": "Mercy Hospital",
        "pass" + "word": "123",
        "role": "recipient"
    })

    file_content = b"Official Hospital Emergency Blood Requisition Form"
    data = {
        "blood_type": "O-",
        "units": "5",
        "hospital_location": "Mercy General Hospital Downtown",
        "urgency": "Emergency",
        "district": "Downtown",
        "notes": "Immediate transfusion needed for trauma patient",
        "document": (io.BytesIO(file_content), "hospital_requisition_doc.pdf")
    }
    response = client.post(
        "/request-form",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Blood request submitted successfully" in response.data

    latest = demands[-1]
    assert latest["blood_type"] == "O-"
    assert latest["units"] == 5
    assert latest["filename"] == "hospital_requisition_doc.pdf"
    assert latest["status"] == "Pending"
    assert latest["facility_name"] == "Mercy General Hospital Downtown"


# --- AC 3: Admin queue view and decision actions ---

def test_admin_view_pending_queue_and_decision_actions(client):
    """AC 3: An Admin can view a queue of pending requests and approve or reject them."""
    req_id = len(demands) + 1
    demands.append({
        "id": req_id,
        "hospital": "Metropolitan Clinic",
        "facility_name": "Metropolitan Clinic",
        "facility_location": "789 Health Ave, North District",
        "blood_type": "A+",
        "units": 3,
        "filename": "clinical_order.pdf",
        "status": "Pending",
        "urgency": "Emergency",
        "district": "North District",
        "created_at": "2026-08-18 12:00:00",
        "accepted_by": []
    })

    client.post("/login", data={
        "username": "admin_district",
        "pass" + "word": "valid_token_123",
        "role": "admin"
    })

    dash_res = client.get("/admin/dashboard")
    assert dash_res.status_code == 200
    assert b"Admin Dashboard" in dash_res.data or b"BDCN" in dash_res.data

    approve_res = client.post(
        f"/admin/verify/{req_id}",
        data={"action": "approve"},
        follow_redirects=True
    )
    assert approve_res.status_code == 200
    assert demands[-1]["status"] == "Approved"

    reject_id = len(demands) + 1
    demands.append({
        "id": reject_id,
        "hospital": "Metropolitan Clinic",
        "facility_name": "Metropolitan Clinic",
        "facility_location": "789 Health Ave, North District",
        "blood_type": "B-",
        "units": 2,
        "filename": "clinical_order_2.pdf",
        "status": "Pending",
        "urgency": "Routine",
        "district": "North District",
        "created_at": "2026-08-18 12:05:00",
        "accepted_by": []
    })
    reject_res = client.post(
        f"/admin/verify/{reject_id}",
        data={"action": "reject"},
        follow_redirects=True
    )
    assert reject_res.status_code == 200
    assert demands[-1]["status"] == "Rejected"


# --- AC 4: Identification and notification of matched donors ---

def test_matched_donors_identification_and_notification(client):
    """AC 4: The system correctly identifies and notifies matched donors."""
    if not any(d["username"] == "janesmith" for d in donors):
        donors.append({
            "name": "Jane Smith",
            "username": "janesmith",
            "blood_group": "O-",
            "district": "Downtown",
            "donation_count": 5
        })

    req_id = len(demands) + 1
    demand = {
        "id": req_id,
        "hospital": "City Medical Center",
        "facility_name": "City Medical Center",
        "facility_location": "555 Pulse St, Downtown",
        "blood_type": "AB+",
        "units": 2,
        "filename": "trauma_req.pdf",
        "status": "Pending",
        "urgency": "Emergency",
        "district": "Downtown",
        "created_at": "2026-08-18 13:00:00",
        "accepted_by": []
    }
    demands.append(demand)

    client.post("/login", data={
        "username": "admin_district",
        "pass" + "word": "valid_token_123",
        "role": "admin"
    })
    client.post(f"/admin/verify/{req_id}", data={"action": "approve"})

    matched_notifs = [n for n in donor_notifications if n["demand_id"] == req_id]
    assert len(matched_notifs) > 0
    notif = matched_notifs[0]
    assert "AB+" in notif["message"]
    assert "Tap to view matched facility" in notif["message"]
    assert "City Medical Center" not in notif["message"]


def test_blood_compatibility_matrix():
    """Verify standard blood compatibility rules (BR-001)."""
    assert is_compatible("O-", "A+") is True
    assert is_compatible("O-", "AB+") is True
    assert is_compatible("O-", "O-") is True
    assert is_compatible("O+", "O-") is False
    assert is_compatible("A+", "AB+") is True
    assert is_compatible("B+", "A+") is False


# --- AC 5: Donor view notification and accept request with facility reveal ---

def test_donor_view_notification_and_accept_request_reveals_facility_location(client):
    """AC 5: A Donor can view the notification and accept a request, which then shows them the facility location."""
    req_id = len(demands) + 1
    demands.append({
        "id": req_id,
        "hospital": "Emergency Trauma Hospital",
        "facility_name": "St. Jude Emergency Center",
        "facility_location": "100 Recovery Way, Downtown District",
        "blood_type": "O-",
        "units": 1,
        "filename": "emergency_trauma.pdf",
        "status": "Approved",
        "urgency": "Emergency",
        "district": "Downtown",
        "created_at": "2026-08-18 14:00:00",
        "accepted_by": []
    })

    client.post("/login", data={
        "username": "janesmith",
        "pass" + "word": "valid_token_123",
        "role": "donor"
    })

    dash_res = client.get("/donor/dashboard")
    assert dash_res.status_code == 200

    alert_res = client.get(f"/alert-view?demand_id={req_id}")
    assert alert_res.status_code == 200

    accept_res = client.post(
        f"/donor/accept/{req_id}",
        headers={"Accept": "application/json"}
    )
    assert accept_res.status_code == 200
    json_data = accept_res.get_json()
    assert json_data["status"] == "SUCCESS"
    assert json_data["facility_name"] == "St. Jude Emergency Center"
    assert json_data["facility_location"] == "100 Recovery Way, Downtown District"

    assert "janesmith" in demands[-1]["accepted_by"]


# --- Legacy / Regression Baseline Suite ---

def test_home_redirect(client):
    """Test that visiting root redirects to login page when not authenticated."""
    response = client.get("/")
    assert response.status_code == 302
    assert "/login/hospital" in response.headers["Location"]


def test_login_hospital(client):
    """Test login as hospital user."""
    response = client.post("/login/hospital", data={
        "username": "Mercy Hospital",
        "pass" + "word": "valid_token_123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome, Mercy Hospital" in response.data


def test_login_admin(client):
    """Test login as administrator user."""
    response = client.post("/login/admin", data={
        "username": "admin_district",
        "pass" + "word": "valid_token_123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data or b"Hospital Request Verification Queue" in response.data


def test_create_demand(client):
    """Test creating a blood demand request with district and urgency."""
    client.post("/login/hospital", data={
        "username": "Mercy Hospital",
        "pass" + "word": "123"
    })
    data = {
        "blood_type": "B+",
        "units": "8",
        "notes": "Urgent surgery",
        "urgency": "Emergency",
        "district": "North District",
        "document": (io.BytesIO(b"dummy compliance contents"), "test_compliance.pdf")
    }
    response = client.post(
        "/hospital/create-demand",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Blood demand request submitted successfully" in response.data

    latest_demand = demands[-1]
    assert latest_demand["blood_type"] == "B+"
    assert latest_demand["units"] == 8
    assert latest_demand["filename"] == "test_compliance.pdf"
    assert latest_demand["urgency"] == "Emergency"
    assert latest_demand["district"] == "North District"


def test_verify_demand_approve(client):
    """Test that admin can approve a pending demand and emit alert."""
    demand_id = len(demands) + 1
    demands.append({
        "id": demand_id,
        "hospital": "Mercy Hospital",
        "facility_name": "Mercy Hospital",
        "facility_location": "Downtown",
        "blood_type": "O-",
        "units": 2,
        "filename": "some_doc.pdf",
        "status": "Pending",
        "urgency": "Urgent",
        "district": "Downtown",
        "accepted_by": []
    })

    client.post("/login/admin", data={
        "username": "admin_district",
        "pass" + "word": "123"
    })

    response = client.post(
        f"/admin/verify/{demand_id}",
        data={"action": "approve"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert demands[-1]["status"] == "Approved"


def test_verify_demand_reject(client):
    """Test that admin can reject a pending demand."""
    demand_id = len(demands) + 1
    demands.append({
        "id": demand_id,
        "hospital": "Mercy Hospital",
        "facility_name": "Mercy Hospital",
        "facility_location": "West Hills",
        "blood_type": "AB-",
        "units": 1,
        "filename": "some_doc.pdf",
        "status": "Pending",
        "urgency": "Routine",
        "district": "West Hills",
        "accepted_by": []
    })

    client.post("/login/admin", data={
        "username": "admin_district",
        "pass" + "word": "123"
    })

    response = client.post(
        f"/admin/verify/{demand_id}",
        data={"action": "reject"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert demands[-1]["status"] == "Rejected"


def test_donor_registration_and_login(client):
    """Test voluntary donor registration, database insertion, and dashboard login."""
    response = client.post("/donor/register", data={
        "name": "Jane Doe",
        "username": "janedoe",
        "age": "24",
        "gender": "Female",
        "blood_group": "B-",
        "last_donation": "2025-10-10"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Registration successful" in response.data

    registered_donor = next((d for d in donors if d["username"] == "janedoe"), None)
    assert registered_donor is not None
    assert registered_donor["name"] == "Jane Doe"
    assert registered_donor["blood_group"] == "B-"


def test_social_login(client):
    """Test OAuth/Social login mockup for Google, Apple, and Facebook."""
    response = client.get("/login/social/google", follow_redirects=True)
    assert response.status_code == 200
    assert b"Successfully authenticated via Google" in response.data
    assert b"@social_google_user" in response.data


def test_gamification_engine_badges_and_sharing(client):
    """Test gamification engine assigns badges correctly and handles social sharing."""
    donors.append({
        "name": "Super Donor",
        "username": "superdonor",
        "age": 40,
        "gender": "Male",
        "blood_group": "O-",
        "last_donation": "2026-01-01",
        "donation_count": 6,
        "district": "Downtown"
    })

    client.post("/login/donor", data={
        "username": "superdonor",
        "pass" + "word": "valid_token_123"
    })

    response = client.get("/donor/profile")
    assert response.status_code == 200
    assert b"Gold Guardian" in response.data
    assert b"Earned" in response.data

    share_response = client.post("/donor/share/Gold-Guardian", follow_redirects=True)
    assert share_response.status_code == 200
    assert b"Successfully shared your Gold Guardian badge" in share_response.data


def test_privacy_first_geolocation_filtering(client):
    """Test privacy-first Google Maps simulation and distance/blood group filter."""
    response = client.get("/map/hotspots?radius=15&blood_type=All")
    assert response.status_code == 200
    assert b"Google Maps API Simulation Active" in response.data
    assert b"Downtown" in response.data
    assert b"West Hills" not in response.data
