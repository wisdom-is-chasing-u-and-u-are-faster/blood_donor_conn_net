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
        data={
            "action": "approve"},
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
        data={
            "action": "reject"},
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


# =========================================================================
# Jira ARCH-4989 Acceptance Criteria & Requirements Test Suite
# =========================================================================

def test_ac1_social_authentication_endpoints(client):
    """
    AC 1: Given a user is on the login screen, they can authenticate using Google, Apple, or Facebook.
    REQ-F-001: Users can register/login via Social Media (Google, Apple, Facebook).
    """
    for provider in ["Google", "Apple", "Facebook"]:
        res = client.post("/api/v1/auth/social", json={
            "provider": provider,
            "email": f"test_{provider.lower()}@example.com",
            "name": f"Test {provider} User",
            "role": "donor"
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["authenticated"] is True
        assert data["provider"] == provider
        assert data["email"] == f"test_{provider.lower()}@example.com"
        assert data["role"] == "donor"


def test_ac2_donor_profile_update(client):
    """
    AC 2: Given a donor is logged in, they can update their profile with blood type and availability.
    REQ-F-002: Donors can register their blood type and location information.
    """
    # Fetch current profile
    res_get = client.get("/api/v1/donors/profile")
    assert res_get.status_code == 200
    profile = res_get.get_json()
    assert "blood_type" in profile

    # Update profile
    update_payload = {
        "blood_type": "O-",
        "location": "San Francisco, CA",
        "available": True
    }
    res_post = client.post("/api/v1/donors/profile", json=update_payload)
    assert res_post.status_code == 200
    updated = res_post.get_json()
    assert updated["status"] == "updated"
    assert updated["donor"]["blood_type"] == "O-"
    assert updated["donor"]["location"] == "San Francisco, CA"
    assert updated["donor"]["available"] is True


def test_ac3_recipient_hotspots_and_search(client):
    """
    AC 3: Given a recipient is logged in, they can view a map of donor hotspots and filter by blood type.
    REQ-F-003: Recipients can search for donors based on blood type and general location.
    REQ-F-004: Display donor locations on a map using clustering (hotspots) without revealing precise addresses.
    """
    # Test hotspot clustering
    res_hotspots = client.get("/api/v1/donors/hotspots")
    assert res_hotspots.status_code == 200
    hotspots_data = res_hotspots.get_json()
    assert "hotspots" in hotspots_data
    assert len(hotspots_data["hotspots"]) >= 3

    for cluster in hotspots_data["hotspots"]:
        # Verify privacy: coarse coordinates rounded to 2 decimal places
        lat_str = str(cluster["latitude"])
        lon_str = str(cluster["longitude"])
        if "." in lat_str:
            assert len(lat_str.split(".")[1]) <= 2
        if "." in lon_str:
            assert len(lon_str.split(".")[1]) <= 2
        assert cluster["donor_count"] > 0
        assert len(cluster["blood_types"]) > 0

    # Test search filtering
    res_search = client.get("/api/v1/donors/search?blood_type=O-")
    assert res_search.status_code == 200
    search_data = res_search.get_json()
    assert "donors" in search_data
    for donor in search_data["donors"]:
        assert donor["blood_type"] == "O-"


def test_req_f_005_connection_request_intake(client):
    """
    REQ-F-005: Recipients can submit a request to connect with a donor, attaching a medical necessity document.
    """
    payload = {
        "recipient_id": "REC-9876",
        "blood_type": "O-",
        "location": "San Francisco, CA",
        "message": "Urgent request for transfusion support.",
        "document_name": "hospital_letter_signed.pdf",
        "document_base64": "JVBERi0xLjQKJ..."
    }
    res = client.post("/api/v1/requests", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert "request_id" in data
    assert data["status"] == "Pending"

    # Verify retrieval
    res_get = client.get(f"/api/v1/requests/{data['request_id']}")
    assert res_get.status_code == 200
    req_details = res_get.get_json()
    assert req_details["document_name"] == "hospital_letter_signed.pdf"
    assert req_details["blood_type"] == "O-"


def test_ac4_admin_verification_approval_and_rejection(client):
    """
    AC 4: Given an admin is logged in, they can see a list of pending requests and approve or reject them.
    REQ-F-006: District Admins can review and approve/reject connection requests.
    """
    # Create request to approve
    res_create = client.post("/api/v1/requests", json={
        "recipient_id": "REC-1111",
        "blood_type": "A+",
        "location": "San Francisco, CA",
        "document_name": "doctor_cert.pdf"
    })
    req_id = res_create.get_json()["request_id"]

    # Admin approves
    res_approve = client.post(f"/api/v1/admin/requests/{req_id}/verify", json={
        "action": "Approve",
        "notes": "Medical necessity verified."
    })
    assert res_approve.status_code == 200
    assert res_approve.get_json()["status"] == "Approved"
    assert res_approve.get_json()["notification_sent"] is True

    # Create request to reject
    res_create2 = client.post("/api/v1/requests", json={
        "recipient_id": "REC-2222",
        "blood_type": "B+",
        "location": "Oakland, CA",
        "document_name": "invalid_doc.pdf"
    })
    req_id2 = res_create2.get_json()["request_id"]

    # Admin rejects
    res_reject = client.post(f"/api/v1/admin/requests/{req_id2}/verify", json={
        "action": "Reject",
        "notes": "Invalid requisition documentation."
    })
    assert res_reject.status_code == 200
    assert res_reject.get_json()["status"] == "Rejected"


def test_req_f_008_admin_2hour_reminders(client):
    """
    REQ-F-008: District Admins receive automated reminders for pending requests older than 2 hours.
    """
    res = client.get("/api/v1/admin/requests/pending")
    assert res.status_code == 200
    data = res.get_json()
    assert "pending_count" in data
    assert "reminders_count" in data
    assert data["reminders_count"] >= 1

    # REQ-10234 is seeded with 3 hours pending
    req_10234 = next((r for r in data["requests"] if r["request_id"] == "REQ-10234"), None)
    assert req_10234 is not None
    assert req_10234["reminder_active"] is True
    assert req_10234["hours_pending"] >= 2.0


def test_req_f_007_secure_notifications(client):
    """
    REQ-F-007: The platform must send secure app notifications for communication.
    """
    res = client.get("/api/v1/notifications")
    assert res.status_code == 200
    data = res.get_json()
    assert "notifications" in data
    assert len(data["notifications"]) >= 2


def test_ui_page_routes(client):
    """Test all self-contained UI page templates render with status 200."""
    pages = [
        "/pages/login.html",
        "/pages/donor-dashboard.html",
        "/pages/recipient-search.html",
        "/pages/request-form.html",
        "/pages/admin-dashboard.html",
        "/pages/admin-request-details.html",
        "/pages/index.html",
        "/login",
        "/donor-dashboard",
        "/recipient-search",
        "/request-form",
        "/admin-dashboard",
        "/admin-request-details",
        "/ui/app"
    ]
    for page in pages:
        response = client.get(page)
        assert response.status_code == 200, f"Page {page} failed with status {response.status_code}"


def test_health_probe(client):
    """Test standard health and readiness probe for Cloud Run / GCP."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "blood_donor_conn_net"
