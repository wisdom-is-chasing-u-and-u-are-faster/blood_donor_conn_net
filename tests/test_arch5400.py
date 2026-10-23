import pytest
from datetime import datetime, timedelta
from app import app, donors, recipient_requests, audit_logs, notifications_store, lat_lng_to_h3_cluster

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test health and readiness endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "bdcn-service"

def test_ac1_social_login_google_apple_facebook(client):
    """AC 1: Users can successfully register and log in via Google, Apple, or Facebook."""
    # Test REST API social login for Google
    res_google = client.post("/api/v1/auth/social", json={
        "provider": "google",
        "email": "alex.doe@gmail.com",
        "name": "Alex Doe",
        "lat": 37.7749,
        "lng": -122.4194
    })
    assert res_google.status_code == 200
    data_g = res_google.get_json()
    assert data_g["status"] == "success"
    assert data_g["role"] == "donor"
    assert "8728" in data_g["h3_cluster"]

    # Test Apple
    res_apple = client.post("/api/v1/auth/social", json={
        "provider": "apple",
        "email": "user@icloud.com",
        "name": "Apple User"
    })
    assert res_apple.status_code == 200
    assert res_apple.get_json()["status"] == "success"

    # Test Facebook
    res_fb = client.post("/api/v1/auth/social", json={
        "provider": "facebook",
        "email": "user@fb.com",
        "name": "FB User"
    })
    assert res_fb.status_code == 200
    assert res_fb.get_json()["status"] == "success"

def test_ac2_submit_blood_request_with_medical_document(client):
    """AC 2: Recipients can submit a new blood request and attach a medical document."""
    res = client.post("/api/v1/requests", json={
        "blood_type": "O+",
        "donation_type": "Whole Blood",
        "urgency": "Urgent",
        "notes": "Emergency bypass surgery scheduled.",
        "document_name": "requisition_scan_2026.pdf",
        "lat": 37.77,
        "lng": -122.42
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "success"
    assert "REQ-" in data["case_id"]
    assert "8728" in data["h3_cluster"]

    # Check request in list
    created_req = next((r for r in recipient_requests if r["case_id"] == data["case_id"]), None)
    assert created_req is not None
    assert created_req["document_name"] == "requisition_scan_2026.pdf"
    assert created_req["status"] == "Pending"

def test_ac3_ac4_admin_adjudicate_and_push_broadcast(client):
    """
    AC 4: District Administrators can approve or reject pending requests from the web portal dashboard.
    AC 3: Donors receive a push notification for new, approved requests in their vicinity.
    """
    # Create request to adjudicate
    req_res = client.post("/api/v1/requests", json={
        "blood_type": "AB-",
        "donation_type": "Whole Blood",
        "urgency": "Urgent",
        "h3_index": "872830828ffffff"
    })
    req_id = req_res.get_json()["request_id"]

    initial_notifs = len(notifications_store)

    # Approve request via admin endpoint
    adj_res = client.post("/api/v1/admin/adjudicate", json={
        "request_id": req_id,
        "action": "approve",
        "reason": "Verified clinical requisition document"
    })
    assert adj_res.status_code == 200
    data = adj_res.get_json()
    assert data["new_status"] == "Approved"

    # Verify notification created
    assert len(notifications_store) == initial_notifs + 1
    latest_notif = notifications_store[-1]
    assert "AB-" in latest_notif["title"]
    assert latest_notif["h3_cluster"] == "872830828ffffff"

def test_ac5_privacy_preserving_h3_clustering_no_raw_coordinates(client):
    """AC 5: User location coordinates are never stored or transmitted in their raw form; H3 clustering is used."""
    lat = 40.7128
    lng = -74.0060
    cluster = lat_lng_to_h3_cluster(lat, lng)
    assert cluster.startswith("8728")
    assert str(lat) not in cluster
    assert str(lng) not in cluster

    # Test nearby requests endpoint sanitization
    res = client.get("/api/v1/requests/nearby?h3=872830828ffffff")
    assert res.status_code == 200
    requests = res.get_json()["requests"]
    for r in requests:
        assert "lat" not in r
        assert "lng" not in r
        assert "raw_coordinates" not in r
        assert "h3_cluster" in r

def test_ac6_donation_cool_off_period_enforcement(client):
    """
    AC 6: The system prevents a donor from logging a donation before the mandatory cool-off period has passed.
    Enforces 56 days for Whole Blood and 14 days for Platelets.
    """
    # Add test donor with whole blood donation 10 days ago
    ten_days_ago = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    donor_user = "cooloff_test_donor"
    donors.append({
        "username": donor_user,
        "name": "Cooloff Donor",
        "blood_group": "O+",
        "last_donation": ten_days_ago,
        "last_whole_blood": ten_days_ago,
        "last_platelets": None,
        "donation_count": 1
    })

    # Attempt to log another Whole Blood donation today (fails 56-day rule)
    res_wb_fail = client.post("/api/v1/donations/log", json={
        "donor_id": donor_user,
        "donation_type": "Whole Blood",
        "donation_date": datetime.now().strftime("%Y-%m-%d")
    })
    assert res_wb_fail.status_code == 400
    data_wb = res_wb_fail.get_json()
    assert "Mandatory cool-off period active" in data_wb["message"]
    assert data_wb["days_remaining"] == 46

    # Attempt after 56 days have passed
    sixty_days_later = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    res_wb_success = client.post("/api/v1/donations/log", json={
        "donor_id": donor_user,
        "donation_type": "Whole Blood",
        "donation_date": sixty_days_later
    })
    assert res_wb_success.status_code == 200
    assert res_wb_success.get_json()["status"] == "success"

def test_variant_a_pages_rendered(client):
    """Verify all Variant-A UI pages load successfully with status 200."""
    pages = [
        "onboarding-login.html",
        "home-dashboard.html",
        "new-request-form.html",
        "user-profile-badges.html",
        "admin-login.html",
        "adjudication-dashboard.html",
        "notifications-inbox.html",
        "request-status-tracker.html"
    ]
    for page in pages:
        res = client.get(f"/pages/{page}")
        assert res.status_code == 200
        assert b"<!DOCTYPE html>" in res.data
