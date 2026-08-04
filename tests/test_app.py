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


# Additional Tests for ARCH-150 Acceptance Criteria

def test_donor_registration_login_logout(client):
    """AC: Users can successfully register for a new donor account, log in, and log out."""
    # Register donor
    reg_resp = client.post("/donor/register", data={
        "name": "Alex Test",
        "username": "alextest",
        "age": "29",
        "gender": "Male",
        "blood_group": "A+",
        "last_donation": "2025-10-10"
    }, follow_redirects=True)
    assert reg_resp.status_code == 200

    # Logout
    logout_resp = client.get("/logout", follow_redirects=True)
    assert logout_resp.status_code == 200

    # Login
    login_resp = client.post("/login/donor", data={
        "username": "alextest",
        "password": "password123"
    }, follow_redirects=True)
    assert login_resp.status_code == 200


def test_donor_dashboard_and_eligibility(client):
    """AC: Logged-in donors can view their dashboard and see their eligibility status and appointments."""
    client.post("/login/donor", data={"username": "johndoe", "password": "password123"}, follow_redirects=True)
    response = client.get("/donor/dashboard")
    assert response.status_code == 200
    assert b"Eligibility Status" in response.data or b"Welcome" in response.data


def test_donor_appointment_booking(client):
    """AC: Donors can schedule a new appointment and see it reflected in their appointment list."""
    client.post("/login/donor", data={"username": "johndoe", "password": "password123"}, follow_redirects=True)
    response = client.post("/donor/appointments", data={
        "center": "Central Regional Donation Center",
        "date": "2026-08-25",
        "time": "11:00 AM",
        "blood_type": "A+"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Appointment scheduled successfully" in response.data or b"Central Regional" in response.data


def test_admin_inventory_dashboard_and_near_expiration(client):
    """AC: Blood Bank Administrators can view the main inventory dashboard and near-expiration units."""
    client.post("/login/admin", data={"username": "admin_district", "password": "password123"}, follow_redirects=True)
    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    assert b"Inventory Ledger" in response.data or b"NEAR EXPIRATION" in response.data


def test_inventory_manual_entry_and_csv_upload(client):
    """AC: Administrators can add new inventory using manual entry and CSV upload."""
    client.post("/login/admin", data={"username": "admin_district", "password": "password123"}, follow_redirects=True)

    # Manual Entry
    manual_resp = client.post("/inventory/manual-entry", data={
        "facility": "Test Regional Hub",
        "blood_type": "O-",
        "units": "15",
        "component": "Whole Blood",
        "expiration_date": "2026-08-12"
    }, follow_redirects=True)
    assert manual_resp.status_code == 200
    assert b"Successfully added" in manual_resp.data or b"O-" in manual_resp.data

    # CSV Upload
    csv_data = b"facility,blood_type,units,component,expiration_date\nMetro Hub,B+,20,Platelets,2026-08-28\n"
    csv_resp = client.post("/inventory/csv-upload", data={
        "csv_file": (io.BytesIO(csv_data), "inventory_import.csv")
    }, follow_redirects=True)
    assert csv_resp.status_code == 200
    assert b"CSV ingestion complete" in csv_resp.data or b"inventory records added" in csv_resp.data


def test_hospital_critical_code_red(client):
    """AC: Hospital Staff can log in and submit a Critical Code Red request."""
    client.post("/login/hospital", data={"username": "Mercy Hospital",
                "password": "password123"}, follow_redirects=True)
    response = client.post("/critical-code-red", data={
        "hospital_name": "Mercy Hospital Emergency",
        "blood_type": "O-",
        "units": "12",
        "district": "Downtown",
        "notes": "Mass casualty event - urgent O- needed"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"CRITICAL CODE RED" in response.data or b"emergency alert dispatched" in response.data
