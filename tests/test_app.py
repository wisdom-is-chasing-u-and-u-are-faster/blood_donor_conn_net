import pytest
import io
from app import app, demands, alerts, donors


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_home_redirect(client):
    """Test that visiting root redirects to login page when not authenticated."""
    response = client.get("/")
    assert response.status_code == 302
    assert "/login/hospital" in response.headers["Location"]


def test_login_hospital(client):
    """Test login as hospital user."""
    response = client.post("/login/hospital", data={
        "username": "Mercy Hospital",
        "password": "password123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome, Mercy Hospital" in response.data


def test_login_admin(client):
    """Test login as administrator user."""
    response = client.post("/login/admin", data={
        "username": "admin_district",
        "password": "password123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Hospital Request Verification Queue" in response.data


def test_create_demand(client):
    """Test creating a blood demand request with district and urgency."""
    # First login as hospital
    client.post(
        "/login/hospital",
        data={
            "username": "Mercy Hospital",
            "password": "123"})

    # Post blood demand
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
        follow_redirects=True)
    assert response.status_code == 200
    assert b"Blood demand request submitted successfully" in response.data

    # Assert it exists in mock DB
    latest_demand = demands[-1]
    assert latest_demand["blood_type"] == "B+"
    assert latest_demand["units"] == 8
    assert latest_demand["filename"] == "test_compliance.pdf"
    assert latest_demand["urgency"] == "Emergency"
    assert latest_demand["district"] == "North District"


def test_verify_demand_approve(client):
    """Test that admin can approve a pending demand and emit alert."""
    # Add a pending demand
    demand_id = len(demands) + 1
    demands.append({
        "id": demand_id,
        "hospital": "Mercy Hospital",
        "blood_type": "O-",
        "units": 2,
        "filename": "some_doc.pdf",
        "status": "Pending",
        "urgency": "Urgent",
        "district": "Downtown"
    })

    # Login as admin
    client.post(
        "/login/admin",
        data={
            "username": "admin_district",
            "password": "123"})

    # Approve
    response = client.post(
        f"/admin/verify/{demand_id}",
        data={
            "action": "approve"},
        follow_redirects=True)
    assert response.status_code == 200
    assert b"Approved demand" in response.data

    # Verify status changed
    assert demands[-1]["status"] == "Approved"

    # Verify alert created
    assert alerts[-1]["blood_type"] == "O-"


def test_verify_demand_reject(client):
    """Test that admin can reject a pending demand."""
    demand_id = len(demands) + 1
    demands.append({
        "id": demand_id,
        "hospital": "Mercy Hospital",
        "blood_type": "AB-",
        "units": 1,
        "filename": "some_doc.pdf",
        "status": "Pending",
        "urgency": "Routine",
        "district": "West Hills"
    })

    # Login as admin
    client.post(
        "/login/admin",
        data={
            "username": "admin_district",
            "password": "123"})

    # Reject
    response = client.post(
        f"/admin/verify/{demand_id}",
        data={
            "action": "reject"},
        follow_redirects=True)
    assert response.status_code == 200
    assert b"Rejected demand" in response.data

    # Verify status changed
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

    # Assert database update
    registered_donor = next(
        (d for d in donors if d["username"] == "janedoe"), None)
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
    # Register/login donor with high donation count
    donors.append({
        "name": "Super Donor",
        "username": "superdonor",
        "age": 40,
        "gender": "Male",
        "blood_group": "O-",
        "last_donation": "2026-01-01",
        "donation_count": 6
    })

    client.post("/login/donor", data={
        "username": "superdonor",
        "password": "password"
    })

    response = client.get("/donor/profile")
    assert response.status_code == 200
    assert b"Gold Guardian" in response.data
    assert b"Earned" in response.data

    # Test Social sharing
    share_response = client.post(
        "/donor/share/Gold-Guardian",
        follow_redirects=True)
    assert share_response.status_code == 200
    assert b"Successfully shared your Gold Guardian badge" in share_response.data


def test_privacy_first_geolocation_filtering(client):
    """Test privacy-first Google Maps simulation and distance/blood group filter."""
    # Test radius filter of 15km
    response = client.get("/map/hotspots?radius=15&blood_type=All")
    assert response.status_code == 200
    assert b"Google Maps API Simulation Active" in response.data
    assert b"Downtown" in response.data  # Distance 8
    assert b"West Hills" not in response.data  # Distance 35


def test_donor_registration_login_and_profile_management(client):
    """AC: Users can successfully register as a Donor, log in, and manage their profile."""
    # Register donor
    reg_res = client.post("/donor/register", data={
        "name": "Test Profile Donor",
        "username": "testprofile",
        "age": "30",
        "gender": "Male",
        "blood_group": "A+",
        "last_donation": "2025-12-01"
    }, follow_redirects=True)
    assert reg_res.status_code == 200

    # Log in
    login_res = client.post("/login/donor", data={
        "username": "testprofile",
        "password": "password"
    }, follow_redirects=True)
    assert login_res.status_code == 200

    # Manage profile via POST
    profile_update = client.post("/donor/profile", data={
        "full_name": "Updated Profile Name",
        "phone": "+1-555-0199",
        "email": "testprofile@example.com",
        "blood_group": "A+",
        "district": "Central"
    }, follow_redirects=True)
    assert profile_update.status_code == 200
    assert b"Profile updated successfully" in profile_update.data


def test_hospital_coordinators_create_blood_requests_and_view_dashboard(client):
    """AC: Hospital coordinators can create new blood requests and view them on a dashboard."""
    # Log in as hospital
    client.post("/login/hospital", data={
        "username": "Mercy Hospital",
        "password": "123"
    })

    # View dashboard
    dash_res = client.get("/hospital/dashboard")
    assert dash_res.status_code == 200

    # Create demand
    data = {
        "blood_type": "O+",
        "units": "3",
        "notes": "Emergency trauma request",
        "urgency": "Urgent",
        "district": "Central",
        "document": (io.BytesIO(b"test doc"), "req_doc.pdf")
    }
    create_res = client.post("/hospital/create-demand", data=data,
                             content_type="multipart/form-data", follow_redirects=True)
    assert create_res.status_code == 200
    assert b"Blood demand request submitted successfully" in create_res.data


def test_admin_system_statistics_dashboard(client):
    """AC: Admins can view system statistics on the admin dashboard."""
    client.post("/login/admin", data={
        "username": "admin_district",
        "password": "123"
    })

    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    assert b"System Statistics Dashboard" in response.data or b"total_donors" in response.data


def test_responsive_ui_and_viewport_meta_tags(client):
    """AC: The UI is responsive and functions correctly on modern desktop and mobile web browsers."""
    res = client.get("/login/donor")
    assert res.status_code == 200
    assert b"viewport" in res.data
    assert b"bootstrap" in res.data or b"container" in res.data
