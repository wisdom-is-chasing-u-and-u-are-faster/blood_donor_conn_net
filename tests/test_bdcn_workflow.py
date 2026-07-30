"""
Acceptance Criteria Verification Test Suite for ARCH-69:
1. Users can successfully register as a Donor, log in, and manage their profile.
2. Hospital coordinators can create new blood requests and view them on a dashboard.
3. Admins can view system statistics on the admin dashboard.
4. The UI is responsive and functions correctly on modern desktop and mobile web browsers.
"""
import io
import pytest
from app import app, donors, demands


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_donor_registration_login_and_profile_management(client):
    """
    AC 1: Users can successfully register as a Donor, log in, and manage their profile.
    """
    # 1. Register donor
    reg_response = client.post("/donor/register", data={
        "name": "Alice Donor",
        "username": "alicedonor",
        "age": "28",
        "gender": "Female",
        "blood_group": "O+",
        "last_donation": "2025-08-15"
    }, follow_redirects=True)
    assert reg_response.status_code == 200
    assert b"Registration successful" in reg_response.data or b"alicedonor" in reg_response.data

    # 2. Login donor
    login_response = client.post("/login/donor", data={
        "username": "alicedonor",
        "password": "password123"
    }, follow_redirects=True)
    assert login_response.status_code == 200
    assert b"Welcome back, Alice Donor" in login_response.data or b"alicedonor" in login_response.data

    # 3. View and manage profile (update name, age, last_donation)
    update_response = client.post("/donor/profile", data={
        "name": "Alice M. Donor",
        "age": "29",
        "gender": "Female",
        "blood_group": "O+",
        "last_donation": "2026-01-10"
    }, follow_redirects=True)
    assert update_response.status_code == 200
    assert b"Profile updated successfully" in update_response.data or b"Alice M. Donor" in update_response.data

    # Verify donor record in state
    updated_donor = next((d for d in donors if d["username"] == "alicedonor"), None)
    assert updated_donor is not None
    assert updated_donor["name"] == "Alice M. Donor"
    assert updated_donor["age"] == 29


def test_hospital_coordinator_request_and_dashboard(client):
    """
    AC 2: Hospital coordinators can create new blood requests and view them on a dashboard.
    """
    # 1. Hospital login
    login_res = client.post("/login/hospital", data={
        "username": "General Hospital",
        "password": "password123"
    }, follow_redirects=True)
    assert login_res.status_code == 200

    # 2. View hospital dashboard
    dash_response = client.get("/hospital/dashboard")
    assert dash_response.status_code == 200
    assert b"Your Blood Demand Requests" in dash_response.data

    # 3. Create new blood demand request with file attachment
    initial_count = len(demands)
    create_data = {
        "blood_type": "A-",
        "units": "5",
        "urgency": "Urgent",
        "district": "Central",
        "notes": "Emergency ICU requirement",
        "document": (io.BytesIO(b"compliance content"), "compliance_icu.pdf")
    }
    create_response = client.post(
        "/hospital/create-demand",
        data=create_data,
        content_type="multipart/form-data",
        follow_redirects=True
    )
    assert create_response.status_code == 200
    assert b"Blood demand request submitted successfully" in create_response.data

    # Verify demand added
    assert len(demands) == initial_count + 1
    new_demand = demands[-1]
    assert new_demand["blood_type"] == "A-"
    assert new_demand["units"] == 5
    assert new_demand["filename"] == "compliance_icu.pdf"


def test_admin_system_statistics_dashboard(client):
    """
    AC 3: Admins can view system statistics on the admin dashboard.
    """
    # 1. Admin login
    client.post("/login/admin", data={
        "username": "admin_master",
        "password": "password123"
    }, follow_redirects=True)

    # 2. Access admin dashboard
    admin_dash_response = client.get("/admin/dashboard")
    assert admin_dash_response.status_code == 200
    assert b"Administrator Statistics Dashboard" in admin_dash_response.data
    assert b"Total Donors" in admin_dash_response.data
    assert b"Total Blood Demands" in admin_dash_response.data
    assert b"Active Emergency Alerts" in admin_dash_response.data


def test_responsive_ui_rendering(client):
    """
    AC 4: The UI is responsive and functions correctly on modern desktop and mobile web browsers.
    """
    # Check viewport meta tags and responsive grid containers in key pages
    pages = ["/login/donor", "/login/hospital", "/donor/register", "/map/hotspots"]
    for page in pages:
        res = client.get(page)
        assert res.status_code == 200
        assert b'name="viewport"' in res.data
        assert b'width=device-width' in res.data
