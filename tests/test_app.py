import os
import io
import pytest
from app import app, demands, alerts, donors

TEST_AUTH_TOKEN = os.environ.get("TEST_SECRET_VAR", "mock_credentials_token")  # pragma: allowlist secret


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
        "password": TEST_AUTH_TOKEN
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome, Mercy Hospital" in response.data


def test_login_admin(client):
    """Test login as administrator user."""
    response = client.post("/login/admin", data={
        "username": "admin_district",
        "password": TEST_AUTH_TOKEN
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
            "password": TEST_AUTH_TOKEN})

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
            "password": TEST_AUTH_TOKEN})

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
            "password": TEST_AUTH_TOKEN})

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
        "password": TEST_AUTH_TOKEN
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

# --- ARCH-405: Recipient Request Submission & Validation Engine Tests ---


def test_validate_blood_request_engine_function():
    """Test standalone validate_blood_request helper function."""
    from app import validate_blood_request

    # Valid request
    valid, err, data = validate_blood_request(
        hospital="City Hospital",
        blood_type="O+",
        units="5",
        filename="doc.pdf",
        urgency="Emergency",
        district="Downtown"
    )
    assert valid is True
    assert err == ""
    assert data["units"] == 5
    assert data["blood_type"] == "O+"
    assert data["status"] == "Pending"

    # Invalid blood group
    valid, err, data = validate_blood_request(
        hospital="City Hospital",
        blood_type="XYZ",
        units="5",
        filename="doc.pdf"
    )
    assert valid is False
    assert "Invalid blood group" in err

    # Negative / zero units
    valid, err, data = validate_blood_request(
        hospital="City Hospital",
        blood_type="A+",
        units="0",
        filename="doc.pdf"
    )
    assert valid is False
    assert "positive integer" in err

    # Missing filename
    valid, err, data = validate_blood_request(
        hospital="City Hospital",
        blood_type="A+",
        units="3",
        filename=None
    )
    assert valid is False
    assert "Medical certification" in err


def test_create_demand_validation_failure_invalid_blood(client):
    """Test submitting demand with invalid blood group fails validation."""
    client.post("/login/hospital", data={"username": "Mercy Hospital", "password": TEST_AUTH_TOKEN})
    data = {
        "blood_type": "INVALID_TYPE",
        "units": "4",
        "urgency": "Standard",
        "district": "Downtown",
        "document": (io.BytesIO(b"dummy content"), "test.pdf")
    }
    response = client.post(
        "/hospital/create-demand",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Invalid blood group" in response.data


def test_create_demand_validation_failure_zero_units(client):
    """Test submitting demand with zero units fails validation."""
    client.post("/login/hospital", data={"username": "Mercy Hospital", "password": TEST_AUTH_TOKEN})
    data = {
        "blood_type": "A+",
        "units": "-2",
        "urgency": "Standard",
        "district": "Downtown",
        "document": (io.BytesIO(b"dummy content"), "test.pdf")
    }
    response = client.post(
        "/hospital/create-demand",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"positive integer" in response.data


def test_api_demands_crud_and_validation(client):
    """Test /api/demands GET and POST endpoints with JSON payload."""
    # Test GET
    get_res = client.get("/api/demands")
    assert get_res.status_code == 200
    json_data = get_res.get_json()
    assert json_data["status"] == "SUCCESS"
    assert "demands" in json_data

    # Test POST valid
    post_res = client.post("/api/demands", json={
        "hospital": "St. Jude",
        "blood_type": "AB+",
        "units": 6,
        "urgency": "Urgent",
        "district": "East Valley",
        "filename": "certificate.pdf"
    })
    assert post_res.status_code == 201
    res_json = post_res.get_json()
    assert res_json["status"] == "SUCCESS"
    assert res_json["demand"]["blood_type"] == "AB+"
    assert res_json["demand"]["units"] == 6

    # Test POST invalid
    invalid_res = client.post("/api/demands", json={
        "hospital": "St. Jude",
        "blood_type": "UNKNOWN",
        "units": 6,
        "filename": "certificate.pdf"
    })
    assert invalid_res.status_code == 400
    assert invalid_res.get_json()["status"] == "INVALID"

# --- ARCH-406: Geolocation Clustering Precision Leak Fix Tests ---


def test_obfuscate_coordinates_precision():
    """Test coordinate obfuscation limits decimals and prevents high precision leak."""
    from app import obfuscate_coordinates

    # High precision GPS (e.g. 6 decimal places = sub-meter precision)
    precise_lat = 37.774929
    precise_lng = -122.419416

    obf_lat, obf_lng = obfuscate_coordinates(precise_lat, precise_lng, max_decimals=2)
    assert obf_lat == 37.77
    assert obf_lng == -122.42

    # String representations or rounding
    assert len(str(obf_lat).split(".")[1]) <= 2
    assert len(str(obf_lng).split(".")[1]) <= 2


def test_sanitize_hotspots_precision_leak_prevention():
    """Test that hotspot clusters returned to client are sanitized and contain coarse regional data."""
    from app import sanitize_hotspots_for_client, raw_hotspots

    sanitized = sanitize_hotspots_for_client(raw_hotspots)
    assert len(sanitized) == len(raw_hotspots)

    for cluster in sanitized:
        assert "centroid_lat" in cluster
        assert "centroid_lng" in cluster
        assert cluster["precision_level"] == "regional_coarse_1km"
        # Verify no donor PII exists in cluster object
        assert "donor_id" not in cluster
        assert "donor_name" not in cluster
        assert "address" not in cluster


def test_api_map_hotspots_endpoint(client):
    """Test /api/map/hotspots API returns coarse, sanitized cluster data."""
    response = client.get("/api/map/hotspots?radius=20&blood_type=All")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "SUCCESS"
    assert data["radius_km"] == 20
    assert "clusters" in data

    for c in data["clusters"]:
        assert c["distance"] <= 20
        assert c["precision_level"] == "regional_coarse_1km"

# --- ARCH-578: BDCN Full UI Pages & Platform Acceptance Tests ---


def test_br001_compatibility_matrix():
    """Test BR-001 blood type compatibility rules."""
    from app import get_compatible_donor_types

    # Universal donor O- can only receive O-
    assert get_compatible_donor_types("O-") == ["O-"]

    # Universal recipient AB+ can receive all blood types
    ab_plus = get_compatible_donor_types("AB+")
    assert len(ab_plus) == 8
    assert "O-" in ab_plus and "AB+" in ab_plus and "A+" in ab_plus

    # A+ can receive A+, A-, O+, O-
    a_plus = get_compatible_donor_types("A+")
    assert set(a_plus) == {"A+", "A-", "O+", "O-"}

    # B- can receive B-, O-
    b_minus = get_compatible_donor_types("B-")
    assert set(b_minus) == {"B-", "O-"}


def test_find_matching_donors_engine():
    """Test matching engine correctly identifies compatible donors."""
    from app import find_matching_donors

    # O- demand (only O- donors match)
    matched = find_matching_donors("O-")
    assert len(matched) >= 1
    for d in matched:
        assert d["blood_group"] == "O-"


def test_unified_login_roles(client):
    """Test unified login endpoint for Admin, Hospital/Recipient, and Donor roles (AC 1)."""
    # Admin login
    admin_res = client.post("/login", data={
        "username": "admin_district",
        "password": TEST_AUTH_TOKEN,
        "role": "admin"
    }, follow_redirects=True)
    assert admin_res.status_code == 200

    # Hospital/Recipient login
    hosp_res = client.post("/login", data={
        "username": "General Hospital",
        "password": TEST_AUTH_TOKEN,
        "role": "hospital"
    }, follow_redirects=True)
    assert hosp_res.status_code == 200

    # Donor login
    donor_res = client.post("/login", data={
        "username": "janesmith",
        "password": TEST_AUTH_TOKEN,
        "role": "donor"
    }, follow_redirects=True)
    assert donor_res.status_code == 200


def test_donor_accept_request_reveals_facility_location(client):
    """Test donor acceptance of request reveals facility location details (AC 5, REQ-F-014, REQ-F-015)."""
    # Login as donor
    client.post("/login", data={"username": "janesmith", "password": TEST_AUTH_TOKEN, "role": "donor"})

    # Accept demand #1
    response = client.post("/donor/accept-request/1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "SUCCESS"
    assert "facility" in data
    assert "General Hospital" in data["facility"]["name"]
    assert "address" in data["facility"]
    assert "contact" in data["facility"]


def test_ui_routes_rendering(client):
    """Test all UI templates render properly without Jinja errors."""
    # Landing page
    landing_res = client.get("/landing")
    assert landing_res.status_code == 200

    # Login page
    login_res = client.get("/login")
    assert login_res.status_code == 200

    # Alerts view
    alert_res = client.get("/alerts/view")
    assert alert_res.status_code == 200

    # Request form
    req_res = client.get("/request/form")
    assert req_res.status_code == 200

    # Admin dashboard (with admin session)
    client.post("/login", data={"username": "admin_district", "password": TEST_AUTH_TOKEN, "role": "admin"})
    admin_dash_res = client.get("/admin/dashboard")
    assert admin_dash_res.status_code == 200

    # Donor dashboard (with donor session)
    client.post("/login", data={"username": "janesmith", "password": TEST_AUTH_TOKEN, "role": "donor"})
    donor_dash_res = client.get("/donor/dashboard")
    assert donor_dash_res.status_code == 200


def test_api_matching_donors_endpoint(client):
    """Test /api/matching/donors API endpoint."""
    response = client.get("/api/matching/donors?blood_type=AB+")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "SUCCESS"
    assert data["requested_blood_type"] == "AB+"
    assert len(data["compatible_donor_types"]) == 8
