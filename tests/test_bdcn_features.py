import pytest
import json
import os
import sys

# Ensure repo root is on python path
repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test the readiness /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"


def test_req_f_001_auth_signup_login_and_social(client):
    """REQ-F-001: Users can sign up and log in using email/password and social providers."""
    # Signup
    signup_payload = {
        "full_name": "Alice Donor",
        "email": "alice@donor.org",
        "password": "SecurePassword123!",
        "role": "donor"
    }
    signup_res = client.post("/api/v1/auth/signup", json=signup_payload)
    assert signup_res.status_code == 201
    assert signup_res.get_json()["status"] == "success"

    # Login
    login_payload = {
        "email": "alice@donor.org",
        "password": "SecurePassword123!"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    assert login_res.get_json()["status"] == "success"

    # Social Login (Google & Facebook)
    google_res = client.post("/api/v1/auth/social", json={"provider": "google", "email": "alice@gmail.com", "name": "Alice G"})
    assert google_res.status_code == 200
    assert google_res.get_json()["provider"] == "google"

    fb_res = client.post("/api/v1/auth/social", json={"provider": "facebook", "email": "alice@fb.com", "name": "Alice FB"})
    assert fb_res.status_code == 200
    assert fb_res.get_json()["provider"] == "facebook"


def test_req_f_002_donor_profile_and_donation_history(client):
    """REQ-F-002: Donors can create and manage profile, blood type, contact info, and donation history."""
    # Get initial profile
    get_res = client.get("/api/v1/donors/profile")
    assert get_res.status_code == 200
    donor = get_res.get_json()["donor"]
    assert "blood_type" in donor
    assert "donation_history" in donor
    assert len(donor["donation_history"]) >= 1

    # Update profile
    update_res = client.post("/api/v1/donors/profile", json={
        "full_name": "Jane Updated",
        "blood_type": "AB-",
        "phone": "+1-555-9999",
        "location": "Uptown Medical Center"
    })
    assert update_res.status_code == 200
    assert update_res.get_json()["profile"]["blood_type"] == "AB-"
    assert update_res.get_json()["profile"]["phone"] == "+1-555-9999"


def test_req_f_003_donor_availability_status(client):
    """REQ-F-003: Donors can set their availability status (e.g., 'Available', 'Unavailable')."""
    res1 = client.post("/api/v1/donors/availability", json={"availability_status": "Unavailable"})
    assert res1.status_code == 200
    assert res1.get_json()["availability_status"] == "Unavailable"

    res2 = client.post("/api/v1/donors/availability", json={"availability_status": "Available"})
    assert res2.status_code == 200
    assert res2.get_json()["availability_status"] == "Available"


def test_req_f_004_recipient_submit_blood_request(client):
    """REQ-F-004: Recipients can submit a request for blood specifying blood type, location, and urgency."""
    req_payload = {
        "recipient_name": "David Miller",
        "blood_type": "B+",
        "units": 2,
        "hospital_name": "St. Jude Hospital",
        "location": "East Valley",
        "urgency": "Emergency",
        "contact_phone": "+1-555-7788"
    }
    res = client.post("/api/v1/requests", json=req_payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "success"
    req_id = data["request_id"]

    # Verify request is created with Pending Admin Review
    detail_res = client.get(f"/api/v1/requests/{req_id}")
    assert detail_res.status_code == 200
    detail = detail_res.get_json()["request"]
    assert detail["blood_type"] == "B+"
    assert detail["status"] == "Pending Admin Review"
    assert detail["urgency"] == "Emergency"


def test_req_f_005_and_006_admin_dashboard_and_approval(client):
    """REQ-F-005 & REQ-F-006: Admin dashboard to view, approve, or reject blood requests."""
    # List pending requests
    list_res = client.get("/api/v1/requests")
    assert list_res.status_code == 200
    all_reqs = list_res.get_json()["requests"]
    assert len(all_reqs) >= 1

    # Admin approves request #1
    action_res = client.post("/api/v1/admin/requests/1/action", json={"action": "approve"})
    assert action_res.status_code == 200
    action_data = action_res.get_json()
    assert action_data["new_status"] == "Approved"
    assert action_data["notified_donors_count"] >= 1


def test_req_f_007_matching_donor_notifications_on_approval(client):
    """REQ-F-007: System finds and notifies nearby, available donors with matching blood type upon approval."""
    action_res = client.post("/api/v1/admin/requests/1/action", json={"action": "approve"})
    assert action_res.status_code == 200
    data = action_res.get_json()
    assert "notified_donors_count" in data
    assert data["notified_donors_count"] > 0


def test_req_f_008_donor_pledge_to_donate(client):
    """REQ-F-008: Donors can pledge to donate in response to a request."""
    pledge_res = client.post("/api/v1/requests/2/pledge", json={
        "donor_name": "Jane Doe",
        "donor_phone": "+1-555-0199"
    })
    assert pledge_res.status_code == 200
    pledge_data = pledge_res.get_json()
    assert pledge_data["status"] == "success"
    assert pledge_data["pledge"]["donor_name"] == "Jane Doe"


def test_req_f_009_secure_anonymized_messaging(client):
    """REQ-F-009: Facilitate secure, anonymized communication between recipient and donor who has pledged."""
    # Send message from recipient
    send_res = client.post("/api/v1/messages", json={
        "request_id": 2,
        "sender_role": "Recipient",
        "content": "Thank you for pledging! Please proceed to Ward 4B upon arrival."
    })
    assert send_res.status_code == 201
    assert send_res.get_json()["status"] == "success"

    # Fetch messages for request #2
    get_res = client.get("/api/v1/messages?request_id=2")
    assert get_res.status_code == 200
    messages = get_res.get_json()["messages"]
    assert len(messages) >= 1
    assert any("Ward 4B" in m["content"] for m in messages)


def test_frontend_pages_and_prototype_serving(client):
    """Test that all self-contained UI pages and prototype index are served cleanly (200 OK)."""
    pages_to_test = [
        "login.html",
        "donor_dashboard.html",
        "donor_profile.html",
        "request_submission.html",
        "admin_dashboard.html",
        "request_details.html",
        "secure_messaging.html",
        "signup.html"
    ]
    for page in pages_to_test:
        res = client.get(f"/pages/{page}")
        assert res.status_code == 200, f"Failed to serve /pages/{page}"
        assert b"<!DOCTYPE html>" in res.data or b"<html" in res.data

    # Prototype index
    proto_res = client.get("/ui/prototype")
    assert proto_res.status_code == 200
    assert b"Blood Donor Connection Network" in proto_res.data
