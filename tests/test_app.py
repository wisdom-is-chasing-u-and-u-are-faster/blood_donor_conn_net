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


# ---------------------------------------------------------------------------
# ARCH-3619 Acceptance Criteria Tests
# ---------------------------------------------------------------------------
def test_health_check_probe(client):
    """Test Cloud Run health check readiness probe (CONSTRAINT-003)."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "bdcn-platform"


def test_ac1_social_media_login_providers(client):
    """AC 1: Users can successfully log in via at least one social media provider."""
    # Test Google Login
    res_google = client.get("/login/social/google", follow_redirects=True)
    assert res_google.status_code == 200
    assert b"Successfully authenticated via Google" in res_google.data

    # Test Apple Login
    res_apple = client.get("/login/social/apple", follow_redirects=True)
    assert res_apple.status_code == 200
    assert b"Successfully authenticated via Apple" in res_apple.data

    # Test Facebook Login
    res_fb = client.get("/login/social/facebook", follow_redirects=True)
    assert res_fb.status_code == 200
    assert b"Successfully authenticated via Facebook" in res_fb.data

    # Test REST API Social Login endpoint
    api_res = client.post("/api/v1/auth/social-login", json={
        "provider": "google",
        "email": "sarah.connor@example.com",
        "name": "Sarah Connor"
    })
    assert api_res.status_code == 200
    assert api_res.get_json()["status"] == "success"


def test_ac2_privacy_preserving_clustered_map(client):
    """AC 2: The main map view displays clustered data points, not individual addresses."""
    # Test HTML view
    res = client.get("/map")
    assert res.status_code == 200
    assert b"Donor Hotspot" in res.data
    assert b"Your privacy is protected" in res.data
    assert b"Precise residential addresses are never shared publicly" in res.data

    # Test REST API clusters endpoint
    api_res = client.get("/api/v1/map/clusters")
    assert api_res.status_code == 200
    json_data = api_res.get_json()
    assert json_data["status"] == "success"
    clusters = json_data["clusters"]
    assert len(clusters) >= 3

    # Verify each cluster provides coarse centroid coordinates and donor count, zero raw street addresses
    for c in clusters:
        assert "centroid_lat" in c
        assert "centroid_lng" in c
        assert "donor_count" in c
        assert "address" not in c
        assert "street" not in c


def test_ac3_profile_document_upload_interface(client):
    """AC 3: A user can access a profile section with an interface to upload a document."""
    # Test accessing profile page
    res_profile = client.get("/profile")
    assert res_profile.status_code == 200
    assert b"Medical Document" in res_profile.data
    assert b"medical-file-input" in res_profile.data

    # Test HTML form upload with multipart file
    upload_data = {
        "file": (io.BytesIO(b"%PDF-1.4 mock medical clearance form"), "mock_blood_clearance.pdf"),
        "document_type": "Serology Test",
        "notes": "Verified clinic attestation"
    }
    upload_res = client.post(
        "/profile/upload", data=upload_data,
        content_type="multipart/form-data", follow_redirects=True
    )
    assert upload_res.status_code == 200
    assert b"mock_blood_clearance.pdf" in upload_res.data

    # Test REST API document upload endpoint
    api_upload_res = client.post("/api/v1/documents/upload", data={
        "file": (io.BytesIO(b"dummy pdf bytes"), "api_clearance.pdf"),
        "document_type": "Eligibility Form",
        "notes": "API test upload"
    }, content_type="multipart/form-data")
    assert api_upload_res.status_code == 201
    assert api_upload_res.get_json()["status"] == "success"
    assert api_upload_res.get_json()["filename"] == "api_clearance.pdf"


def test_ac4_functional_achievements_gamification_screen(client):
    """AC 4: The application includes a functional achievements/gamification screen."""
    # Test HTML achievements view
    res = client.get("/achievements")
    assert res.status_code == 200
    assert b"Donor Gamification Engine" in res.data
    assert b"First Drop" in res.data
    assert b"Lifesaver" in res.data

    # Test REST API achievements endpoint
    api_res = client.get("/api/v1/achievements")
    assert api_res.status_code == 200
    data = api_res.get_json()
    assert data["status"] == "success"
    assert "achievements" in data
    assert len(data["achievements"]) >= 4

    # Test Social sharing endpoint
    share_res = client.post("/api/v1/achievements/share", json={
        "achievement_id": "lifesaver",
        "platform": "twitter"
    })
    assert share_res.status_code == 200
    assert share_res.get_json()["status"] == "success"
    assert "share_url" in share_res.get_json()


def test_ac5_screens_linked_and_navigable(client):
    """AC 5: All screens in the full UI preview are linked and navigable."""
    screens = [
        "/index",
        "/preview",
        "/login",
        "/dashboard",
        "/map",
        "/profile",
        "/achievements",
        "/settings"
    ]
    for path in screens:
        res = client.get(path)
        assert res.status_code == 200, f"Screen '{path}' failed with status {res.status_code}"
