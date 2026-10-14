import sys
from pathlib import Path

# Ensure local repository root is at the head of sys.path
_repo_dir = str(Path(__file__).resolve().parent.parent)
if _repo_dir in sys.path:
    sys.path.remove(_repo_dir)
sys.path.insert(0, _repo_dir)

import io  # noqa: E402
import pytest  # noqa: E402
from app import app, demands, donors  # noqa: E402


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


# =========================================================================
# Acceptance Criteria 1: Users can successfully log in via Google, Apple, or Facebook
# =========================================================================

def test_ac1_social_login_google_apple_facebook(client):
    """AC 1: Users can successfully log in via Google, Apple, or Facebook."""
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

    # Test REST API Social Auth Endpoint
    api_res = client.get("/api/v1/auth/social/google")
    assert api_res.status_code == 200
    data = api_res.get_json()
    assert data["status"] == "authenticated"
    assert data["provider"] == "google"
    assert "user" in data


# =========================================================================
# Acceptance Criteria 2: Recipient user can view donor hotspots and filter by proximity
# =========================================================================

def test_ac2_recipient_view_hotspot_map_and_proximity_filter(client):
    """AC 2: A logged-in 'Recipient' user can view a map of donor hotspots and filter them by proximity."""
    # Authenticate as recipient
    with client.session_transaction() as sess:
        sess["username"] = "recipient_user"
        sess["role"] = "recipient"

    # View map with proximity filter (10 km)
    res_10km = client.get("/recipient/discovery-map?radius=10&blood_type=All")
    assert res_10km.status_code == 200
    assert b"Google Maps SDK Simulation Active" in res_10km.data
    assert b"Downtown" in res_10km.data  # 8 km
    assert b"West Hills" not in res_10km.data  # 35 km

    # Test District Fallback Table View (REQ-F-011)
    assert b"District Fallback View (REQ-F-011)" in res_10km.data

    # Test REST API for Hotspots with privacy-masked coordinates (REQ-F-010)
    api_res = client.get("/api/v1/donors/hotspots?radius=25&blood_type=All")
    assert api_res.status_code == 200
    data = api_res.get_json()
    assert data["radius_km"] == 25
    assert len(data["hotspots"]) > 0
    first_hotspot = data["hotspots"][0]
    assert "privacy_masked_coords" in first_hotspot
    assert "latitude_coarse" in first_hotspot["privacy_masked_coords"]
    assert "longitude_coarse" in first_hotspot["privacy_masked_coords"]


# =========================================================================
# Acceptance Criteria 3: Recipient user can create a blood donation request
# =========================================================================

def test_ac3_recipient_create_blood_request_with_document(client):
    """AC 3: A logged-in 'Recipient' user can create a blood donation request with document upload."""
    with client.session_transaction() as sess:
        sess["username"] = "sarah_recipient"
        sess["role"] = "recipient"

    # Check GET request form page
    form_res = client.get("/recipient/request")
    assert form_res.status_code == 200
    assert b"Request Blood" in form_res.data
    assert b"Proof of Medical Necessity" in form_res.data

    # Submit request with prescription document
    doc_payload = {
        "blood_type": "AB-",
        "units": "3",
        "urgency": "Critical",
        "district": "Downtown",
        "notes": "Emergency surgery patient at Downtown Medical",
        "document": (io.BytesIO(b"%PDF-1.4 clinical prescription data"), "physician_request.pdf")
    }
    post_res = client.post(
        "/recipient/request",
        data=doc_payload,
        content_type="multipart/form-data",
        follow_redirects=True
    )
    assert post_res.status_code == 200
    assert b"Blood donation request submitted successfully" in post_res.data

    # Verify demand added to in-memory database
    latest_req = demands[-1]
    assert latest_req["blood_type"] == "AB-"
    assert latest_req["units"] == 3
    assert latest_req["urgency"] == "Critical"
    assert latest_req["filename"] == "physician_request.pdf"

    # Test REST API creation endpoint
    api_post = client.post("/api/v1/requests", json={
        "blood_type": "O-",
        "units": 2,
        "urgency": "Emergency",
        "district": "North District",
        "notes": "Trauma encounter requisition"
    })
    assert api_post.status_code == 201
    assert api_post.get_json()["schema"]["blood_type"] == "O-"


# =========================================================================
# Acceptance Criteria 4: Donor user can view a list of active donation requests
# =========================================================================

def test_ac4_donor_view_active_donation_requests(client):
    """AC 4: A logged-in 'Donor' user can view a list of active donation requests."""
    # Ensure there is an active requisition in demands
    test_id = len(demands) + 1
    demands.append({
        "id": test_id,
        "hospital": "City Memorial Hospital",
        "blood_type": "A-",
        "units": 2,
        "filename": "requisition.pdf",
        "status": "Pending",
        "urgency": "High",
        "district": "Downtown"
    })

    # Log in as donor
    with client.session_transaction() as sess:
        sess["username"] = "janesmith"
        sess["role"] = "donor"

    # View Donor Hub / Dashboard
    res = client.get("/donor/dashboard")
    assert res.status_code == 200
    assert b"Active Donation Requests (AC 4)" in res.data
    assert b"City Memorial Hospital" in res.data
    assert b"A-" in res.data
    assert b"High" in res.data
    assert b"Respond to Alert" in res.data

    # Check REST API for active requests
    api_res = client.get("/api/v1/requests")
    assert api_res.status_code == 200
    requests_list = api_res.get_json()["requests"]
    assert any(r["hospital"] == "City Memorial Hospital" for r in requests_list)


# =========================================================================
# Acceptance Criteria 5: Deployable to Web & placeholder shells for iOS/Android
# =========================================================================

def test_ac5_deployable_web_and_mobile_shells(client):
    """AC 5: Deployable to Web (responsive site) and have placeholder shells for iOS and Android."""
    # 1. Web readiness: verify health probe and key responsive views
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.get_json()["status"] == "ok"

    overview_res = client.get("/overview")
    assert overview_res.status_code == 200
    assert b"Blood Donor Connection Network" in overview_res.data

    role_res = client.get("/role-selection")
    assert role_res.status_code == 200
    assert b"Choose Your Role" in role_res.data

    # 2. Verify iOS mobile placeholder shell existence
    repo_root = Path(app.root_path)
    ios_plist = repo_root / "mobile" / "ios" / "Info.plist"
    ios_delegate = repo_root / "mobile" / "ios" / "AppDelegate.swift"
    assert ios_plist.exists(), "iOS Info.plist must exist"
    assert ios_delegate.exists(), "iOS AppDelegate.swift must exist"
    assert "org.bdcn.health.donorconnect" in ios_plist.read_text()

    # 3. Verify Android mobile placeholder shell existence
    android_manifest = repo_root / "mobile" / "android" / "AndroidManifest.xml"
    android_activity = repo_root / "mobile" / "android" / "MainActivity.kt"
    assert android_manifest.exists(), "Android AndroidManifest.xml must exist"
    assert android_activity.exists(), "Android MainActivity.kt must exist"
    assert "org.bdcn.health.donorconnect" in android_manifest.read_text()

    # 4. Verify 12-factor deployment configuration files exist
    assert (repo_root / ".env.example").exists(), ".env.example must exist"
    assert (repo_root / "docker-compose.yml").exists(), "docker-compose.yml must exist"
    assert (repo_root / "Dockerfile").exists(), "Dockerfile must exist"
    assert (repo_root / "db" / "schema.sql").exists(), "db/schema.sql must exist"


# =========================================================================
# Additional End-to-End & Backward-Compatibility Verification Tests
# =========================================================================

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
    client.post("/login/hospital", data={"username": "Mercy Hospital", "password": "123"})
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
    client.post("/login/admin", data={"username": "admin_district", "password": "123"})
    response = client.post(f"/admin/verify/{demand_id}", data={"action": "approve"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Approved demand" in response.data
    assert demands[-1]["status"] == "Approved"


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
    client.post("/login/admin", data={"username": "admin_district", "password": "123"})
    response = client.post(f"/admin/verify/{demand_id}", data={"action": "reject"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Rejected demand" in response.data
    assert demands[-1]["status"] == "Rejected"


def test_donor_registration_and_login(client):
    """Test voluntary donor registration and profile redirection."""
    response = client.post("/donor/register", data={
        "name": "Jane Doe",
        "username": "janedoe_new",
        "age": "24",
        "gender": "Female",
        "blood_group": "B-",
        "last_donation": "2025-10-10"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Registration successful" in response.data
    registered = next((d for d in donors if d["username"] == "janedoe_new"), None)
    assert registered is not None
    assert registered["blood_group"] == "B-"


def test_gamification_profile_and_share(client):
    """Test gamification progression profile and social sharing."""
    with client.session_transaction() as sess:
        sess["username"] = "janesmith"
        sess["role"] = "donor"

    res_profile = client.get("/profile/gamification")
    assert res_profile.status_code == 200
    assert b"Gamification & Impact Stats (REQ-F-002)" in res_profile.data
    assert b"Gold Guardian" in res_profile.data

    # Test badge sharing
    res_share = client.post("/donor/share/Gold-Guardian", follow_redirects=True)
    assert res_share.status_code == 200
    assert b"Successfully shared your Gold Guardian badge" in res_share.data


def test_notifications_center(client):
    """Test secure notification center view (REQ-F-006)."""
    res = client.get("/notifications")
    assert res.status_code == 200
    assert b"Secure Notification Center (REQ-F-006)" in res.data
    assert b"URGENT TRAUMA ALERT" in res.data


def test_districts_api(client):
    """Test districts fallback API endpoint (REQ-F-011)."""
    res = client.get("/api/v1/districts")
    assert res.status_code == 200
    districts = res.get_json()["districts"]
    assert len(districts) >= 5
    assert any(d["name"] == "Downtown" for d in districts)
