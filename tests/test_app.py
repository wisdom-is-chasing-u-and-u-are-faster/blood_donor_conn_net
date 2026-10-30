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
    client.post(
        "/login/hospital",
        data={
            "username": "Mercy Hospital",
            "password": "123"})

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
        "blood_type": "O-",
        "units": 2,
        "filename": "some_doc.pdf",
        "status": "Pending",
        "urgency": "Urgent",
        "district": "Downtown"
    })

    client.post(
        "/login/admin",
        data={
            "username": "admin_district",
            "password": "123"})

    response = client.post(
        f"/admin/verify/{demand_id}",
        data={"action": "approve"},
        follow_redirects=True)
    assert response.status_code == 200
    assert b"Approved demand" in response.data
    assert demands[-1]["status"] == "Approved"
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

    client.post(
        "/login/admin",
        data={
            "username": "admin_district",
            "password": "123"})

    response = client.post(
        f"/admin/verify/{demand_id}",
        data={"action": "reject"},
        follow_redirects=True)
    assert response.status_code == 200
    assert b"Rejected demand" in response.data
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


def test_gamification_engine_badges_and_sharing(client):
    """Test gamification engine assigns badges correctly and handles social sharing."""
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

    share_response = client.post(
        "/donor/share/Gold-Guardian",
        follow_redirects=True)
    assert share_response.status_code == 200
    assert b"Successfully shared your Gold Guardian badge" in share_response.data


def test_privacy_first_geolocation_filtering(client):
    """Test privacy-first Google Maps simulation and distance/blood group filter."""
    response = client.get("/map/hotspots?radius=15&blood_type=All")
    assert response.status_code == 200
    assert b"Google Maps API Simulation Active" in response.data
    assert b"Downtown" in response.data
    assert b"West Hills" not in response.data


# ============================================================================
# ARCH-6455 NEW FEATURE TESTS: Auth, OAuth2, Dashboards & Role-Based Filtering
# ============================================================================

def test_arch_6455_health_check(client):
    """AC: Container readiness /health probe returns 200 and healthy status."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "bdcn_platform"


def test_arch_6455_dedicated_login_page_get(client):
    """AC: A user can successfully log in via the Login screen (REQ-F-001)."""
    res = client.get("/login")
    assert res.status_code == 200
    assert b"BDCN Portal Login" in res.data
    assert b"Select Role" in res.data
    assert b"Sign in with Google" in res.data


def test_arch_6455_dedicated_login_post_donor(client):
    """AC: A user can successfully log in via Login screen as Donor and redirect to donor dashboard."""
    res = client.post("/login", data={
        "username": "janesmith",
        "password": "secretpassword",
        "role": "donor"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Donor Dashboard" in res.data
    assert b"Compatible Blood Demands" in res.data


def test_arch_6455_dedicated_login_post_recipient(client):
    """AC: A user can successfully log in via Login screen as Recipient and redirect to recipient dashboard."""
    res = client.post("/login", data={
        "username": "alex_recipient",
        "password": "secretpassword",
        "role": "recipient"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Recipient Request Tracker" in res.data
    assert b"My Blood Requests" in res.data


def test_arch_6455_dedicated_login_post_hospital_admin(client):
    """AC: A user can successfully log in via Login screen as Hospital/Admin and access supply chain dashboard."""
    res = client.post("/login", data={
        "username": "mercy_hospital_admin",
        "password": "secretpassword",
        "role": "hospital"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Hospital Logistics & Blood Supply Chain Management" in res.data


def test_arch_6455_api_auth_login_and_oauth2(client):
    """AC: OAuth2 session management and API login return JSON token/session."""
    # Test API username/password login
    res = client.post("/api/v1/auth/login", json={
        "username": "janesmith",
        "password": "pass123",
        "role": "donor"
    })
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["role"] == "donor"
    assert json_data["redirect_url"] == "/donor/dashboard"

    # Test OAuth2 session endpoint
    res_oauth = client.post("/api/v1/auth/oauth2", json={
        "provider": "google",
        "role": "donor"
    })
    assert res_oauth.status_code == 200
    oauth_data = res_oauth.get_json()
    assert oauth_data["success"] is True
    assert "oauth2_google_user" in oauth_data["username"]


def test_arch_6455_donor_dashboard_compatible_requests(client):
    """AC: The Donor Dashboard correctly displays compatible blood requests (REQ-F-002)."""
    # Jane Smith is O- (universal red cell donor, can donate to all types)
    client.post("/login", data={"username": "janesmith", "password": "123", "role": "donor"})
    res = client.get("/donor/dashboard")
    assert res.status_code == 200
    assert b"Donor Dashboard" in res.data
    assert b"Compatible Blood Demands" in res.data
    assert b"A+" in res.data or b"O-" in res.data


def test_arch_6455_recipient_dashboard_and_create_request(client):
    """AC: The Recipient Dashboard allows users to track their requests (REQ-F-003)."""
    client.post("/login", data={"username": "test_recipient", "password": "123", "role": "recipient"})
    res = client.get("/recipient/dashboard")
    assert res.status_code == 200
    assert b"Recipient Request Tracker" in res.data

    # Create new blood request from Recipient Dashboard
    create_res = client.post("/recipient/create-request", data={
        "blood_type": "B+",
        "units": "3",
        "urgency": "Urgent",
        "district": "East Valley"
    }, follow_redirects=True)
    assert create_res.status_code == 200
    assert b"Blood request submitted successfully" in create_res.data
    assert b"B+" in create_res.data


def test_arch_6455_hospital_admin_dashboard(client):
    """AC: The Hospital Admin Dashboard provides necessary tools to manage blood supply chain (REQ-F-004)."""
    client.post("/login", data={"username": "admin_district", "password": "123", "role": "admin"})
    res = client.get("/admin/dashboard")
    assert res.status_code == 200
    assert b"Supply Chain Demand Ledger" in res.data
    assert b"Active Demands" in res.data
    assert b"Pending Review" in res.data


def test_arch_6455_role_based_blood_request_filtering_api(client):
    """AC: Role-based blood request filtering (Donor, Recipient, Hospital Admin views)."""
    # 1. Hospital Admin / All view
    res_admin = client.get("/api/v1/requests?role=admin")
    assert res_admin.status_code == 200
    admin_data = res_admin.get_json()
    assert admin_data["role"] == "admin"
    assert len(admin_data["requests"]) >= 2

    # 2. Donor view (compatible requests)
    res_donor = client.get("/api/v1/requests?role=donor")
    assert res_donor.status_code == 200
    donor_data = res_donor.get_json()
    assert donor_data["role"] == "donor"
    assert isinstance(donor_data["requests"], list)

    # 3. Create request via API
    res_post = client.post("/api/v1/requests", json={
        "blood_type": "AB+",
        "units": 2,
        "urgency": "Emergency",
        "district": "Downtown"
    })
    assert res_post.status_code == 201
    post_data = res_post.get_json()
    assert post_data["status"] == "Pending"
