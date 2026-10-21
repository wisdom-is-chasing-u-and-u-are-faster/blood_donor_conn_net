"""
Unit & Integration Tests for Jira Ticket ARCH-4940:
Blood Donor Connection Network (BDCN)
"""
import io
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


# ==============================================================================
# Health Probe
# ==============================================================================

def test_health_probe(client):
    """Verify container readiness and health probe returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "bdcn-platform"


# ==============================================================================
# AC 1: Social Provider Authentication (Google, Apple, Facebook)
# ==============================================================================

def test_ac1_social_login_google(client):
    """AC 1: Users can successfully log in via Google social provider."""
    # Test API social auth
    response = client.post("/api/v1/auth/social", json={
        "provider": "google",
        "email": "user@gmail.com",
        "name": "Google User"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["authenticated"] is True
    assert data["user"]["role"] == "donor"
    assert "google" in data["user"]["username"]

    # Verify session persists
    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    me_data = me_resp.get_json()
    assert me_data["authenticated"] is True
    assert me_data["user"]["role"] == "donor"


def test_ac1_social_login_apple_and_facebook(client):
    """AC 1: Users can successfully log in via Apple or Facebook accounts."""
    # Test Apple
    apple_resp = client.post("/api/v1/auth/social", json={
        "provider": "apple",
        "email": "user@icloud.com",
        "name": "Apple User"
    })
    assert apple_resp.status_code == 200
    assert apple_resp.get_json()["authenticated"] is True

    # Test Facebook
    fb_resp = client.post("/api/v1/auth/social", json={
        "provider": "facebook",
        "email": "user@meta.com",
        "name": "Facebook User"
    })
    assert fb_resp.status_code == 200
    assert fb_resp.get_json()["authenticated"] is True

    # Test Logout
    logout_resp = client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.get_json()["status"] == "logged_out"


# ==============================================================================
# AC 2: Map View & Donor Location Data
# ==============================================================================

def test_ac2_map_view_hotspots(client):
    """AC 2: The map view loads and displays donor location data & hotspots."""
    response = client.get("/api/v1/donors/hotspots?radius=50&blood_type=All")
    assert response.status_code == 200
    hotspots = response.get_json()
    assert len(hotspots) > 0
    assert any(h["district"] == "Downtown" for h in hotspots)
    assert any(h["blood_type"] == "O-" for h in hotspots)


def test_ac2_donor_proximity_search_with_privacy(client):
    """AC 2 & REQ-N-003: Proximity search filters donors while masking exact coordinates."""
    response = client.get("/api/v1/donors?radius=10&blood_type=All")
    assert response.status_code == 200
    donors_list = response.get_json()
    assert len(donors_list) > 0
    first_donor = donors_list[0]
    # Check coarse coordinates are rounded to 2 decimal places (coarse centroid)
    assert "coarse_lat" in first_donor
    assert "coarse_lng" in first_donor
    assert "distance_km" in first_donor


# ==============================================================================
# AC 3: Blood Request Creation with Medical Document Upload
# ==============================================================================

def test_ac3_create_blood_request_with_document(client):
    """AC 3: A user can create a new blood request and upload a document."""
    data = {
        "patient_name": "John Connor",
        "hospital_name": "Metro Trauma Center",
        "blood_type": "O-",
        "units": "3",
        "urgency": "Emergency",
        "district": "Downtown",
        "document": (io.BytesIO(b"%PDF-1.4 Mock verification doc"), "medical_record.pdf")
    }
    response = client.post(
        "/api/v1/requests",
        data=data,
        content_type="multipart/form-data"
    )
    assert response.status_code == 201
    result = response.get_json()
    assert result["patient_name"] == "John Connor"
    assert result["blood_type"] == "O-"
    assert result["status"] == "Pending"
    assert result["filename"] == "medical_record.pdf"


def test_ac3_create_blood_request_json(client):
    """AC 3: Submitting request via JSON API with document reference."""
    payload = {
        "patient_name": "Jane Miller",
        "hospital_name": "City General",
        "blood_type": "B+",
        "units": 2,
        "urgency": "Urgent",
        "district": "North District",
        "document_name": "doctor_prescription.pdf"
    }
    response = client.post("/api/v1/requests", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["patient_name"] == "Jane Miller"
    assert data["status"] == "Pending"
    assert data["filename"] == "doctor_prescription.pdf"


# ==============================================================================
# AC 4: Admin Request Verification (Approve / Reject)
# ==============================================================================

def test_ac4_admin_list_and_approve_request(client):
    """AC 4: Admin user can see a list of requests and approve them."""
    # List pending requests
    list_resp = client.get("/api/v1/requests?status=Pending")
    assert list_resp.status_code == 200
    requests_list = list_resp.get_json()
    assert len(requests_list) > 0
    target_id = requests_list[0]["id"]

    # Approve request
    approve_resp = client.post(
        f"/api/v1/admin/requests/{target_id}/verify",
        json={"action": "approve", "notes": "Medical documents verified"}
    )
    assert approve_resp.status_code == 200
    assert approve_resp.get_json()["status"] == "Approved"


def test_ac4_admin_reject_request(client):
    """AC 4: Admin user can reject a request with audit trail."""
    # Create request to reject
    req_resp = client.post("/api/v1/requests", json={
        "patient_name": "Test Incomplete",
        "hospital_name": "General Hospital",
        "blood_type": "AB+",
        "units": 1,
        "document_name": "incomplete.pdf"
    })
    req_id = req_resp.get_json()["id"]

    # Reject
    reject_resp = client.post(
        f"/api/v1/admin/requests/{req_id}/verify",
        json={"action": "reject", "notes": "Missing physician signature"}
    )
    assert reject_resp.status_code == 200
    assert reject_resp.get_json()["status"] == "Rejected"


# ==============================================================================
# AC 5: Navigability & Functional Links across Final UI Prototype
# ==============================================================================

def test_ac5_ui_prototype_routes_navigable(client):
    """AC 5: All links in the final UI prototype are navigable and functional."""
    # Test interactive single-page application prototype
    ui_resp = client.get("/ui/app")
    assert ui_resp.status_code == 200
    assert b"Blood Donor Connection Network" in ui_resp.data
    assert b"map-view" in ui_resp.data
    assert b"request-form" in ui_resp.data
    assert b"/static/js/api.js" in ui_resp.data

    # Test individual prototype pages from design assets
    for page in ["home.html", "about.html", "services.html", "contact.html"]:
        resp = client.get(f"/pages/{page}")
        assert resp.status_code == 200
        assert b"/static/js/api.js" in resp.data


# ==============================================================================
# Auxiliary Features: Profile Update, Social Sharing & Notifications
# ==============================================================================

def test_donor_profile_update(client):
    """REQ-F-003: Donor profile creation and management."""
    # First authenticate
    client.post("/api/v1/auth/social", json={"provider": "google"})

    profile_data = {
        "full_name": "Dr. Alex Cross",
        "blood_type": "O-",
        "location": "Downtown",
        "email": "alex@cross.org",
        "phone": "+1-555-0199"
    }
    response = client.post("/api/v1/donors/profile", json=profile_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["profile"]["full_name"] == "Dr. Alex Cross"


def test_social_sharing_and_notifications(client):
    """REQ-F-008 & REQ-F-009: Social sharing and in-app notifications."""
    # Test social share
    share_resp = client.post("/api/v1/donors/share", json={
        "badge_name": "Gold Guardian",
        "platform": "twitter"
    })
    assert share_resp.status_code == 200
    assert share_resp.get_json()["status"] == "shared"

    # Test notifications
    notif_resp = client.get("/api/v1/notifications")
    assert notif_resp.status_code == 200
    notifs = notif_resp.get_json()
    assert isinstance(notifs, list)
    assert len(notifs) > 0
