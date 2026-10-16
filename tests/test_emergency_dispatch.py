import os
"""
Full-stack and unit test suite for BDCN Emergency Dispatch & Donor Portal workflows.
Tests all Acceptance Criteria and API contracts for ARCH-4675.
"""
import pytest
import json
from app import app, digital_passes_store


@pytest.fixture
def client():
    app.config.update({"TESTING": bool(os.environ.get("TESTING", True)), "WTF_CSRF_ENABLED": False})
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test health and readiness probe."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "blood_donor_conn_net"


def test_clinical_fhir_emergency_requisition_endpoint(client):
    """
    [ARCH-4675-AC4]: The system must expose a secure REST/FHIR endpoint
    for clinical staff to submit new emergency requisitions.
    """
    # 1. Ingest FHIR / REST requisition
    payload = {
        "resourceType": "SupplyRequest",
        "hospital_name": "St. Jude Trauma Center",
        "hospital_id": "HOSP-992",
        "blood_type": "B-",
        "units": 6,
        "urgency": "Emergency",
        "radius_km": 15.0,
        "notes": "Mass casualty emergency transfusion",
        "latitude": 37.7833,
        "longitude": -122.4167
    }
    res = client.post(
        "/api/v1/clinical/emergency-requests",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert res.status_code == 201
    data = res.get_json()
    assert "request_id" in data
    assert data["status"] == "broadcast"
    assert data["matched_donors_count"] >= 1
    req_id = data["request_id"]

    # 2. Query list of emergency requests
    list_res = client.get("/api/v1/clinical/emergency-requests")
    assert list_res.status_code == 200
    list_data = list_res.get_json()
    assert any(r["request_id"] == req_id for r in list_data["requests"])

    # 3. Query single emergency request
    single_res = client.get(f"/api/v1/clinical/emergency-requests/{req_id}")
    assert single_res.status_code == 200
    assert single_res.get_json()["blood_type"] == "B-"


def test_donor_notification_on_broadcast(client):
    """
    [ARCH-4675-AC1]: Given a donor is logged in, when an emergency request is broadcast,
    the donor must receive a notification on their mobile interface.
    """
    # Login donor to mobile portal
    login_res = client.post("/donor/portal/login", data={
        "username": "janesmith",
        "password": "mock_donor_auth"  # pragma: allowlist secret
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b"Urgent Donation Request" in login_res.data
    assert b"A patient's life is on the line" in login_res.data


def test_donor_view_details_and_respond(client):
    """
    [ARCH-4675-AC2]: Given an emergency notification is received, the donor must be able
    to view request details and confirm or decline participation.
    """
    # Access emergency response details view
    view_res = client.get("/donor/portal/emergency-response")
    assert view_res.status_code == 200
    assert b"Request Details" in view_res.data
    assert b"Can you donate now?" in view_res.data
    assert b"Yes, I can donate" in view_res.data
    assert b"No, I'm unable to" in view_res.data

    # Submit response via REST API endpoint
    api_res = client.post(
        "/api/v1/donors/emergency-responses",
        data=json.dumps({
            "request_id": "REQ-EMERG-2026-001",
            "donor_id": "DN-A8C4-E02B",
            "action": "declined"
        }),
        content_type="application/json"
    )
    assert api_res.status_code == 200
    assert api_res.get_json()["status"] == "declined"


def test_digital_check_in_pass_and_qr_code(client):
    """
    [ARCH-4675-AC3]: When a donor confirms participation, a unique, time-sensitive
    digital check-in pass (QR code) must be generated and displayed.
    """
    # Donor confirms donation via web form
    confirm_res = client.post("/donor/portal/respond", data={
        "request_id": "REQ-EMERG-2026-001",
        "action": "confirmed"
    }, follow_redirects=True)

    assert confirm_res.status_code == 200
    assert b"Your Digital Donor Pass" in confirm_res.data
    assert b"Appointment Details" in confirm_res.data
    assert b"QR Code for check-in" in confirm_res.data
    assert b"Emergency Transfusion Center" in confirm_res.data

    # Verify pass details via REST API endpoint
    latest_pass = digital_passes_store[0]
    pass_id = latest_pass["pass_id"]
    api_pass_res = client.get(f"/api/v1/donors/check-in-pass/{pass_id}")
    assert api_pass_res.status_code == 200
    pdata = api_pass_res.get_json()
    assert pdata["pass_id"] == pass_id
    assert "BDCN:PASS:" in pdata["qr_code_data"]
    assert pdata["status"] == "ACTIVE"


def test_mockup_parity_redirects(client):
    """Test that static mockup URLs redirect cleanly to respective portal views."""
    res1 = client.get("/login.html")
    assert res1.status_code == 302
    assert "/donor/portal/login" in res1.headers["Location"]

    res2 = client.get("/emergency_response.html")
    assert res2.status_code == 302
    assert "/donor/portal/emergency-response" in res2.headers["Location"]

    res3 = client.get("/check_in_pass.html")
    assert res3.status_code == 302
    assert "/donor/portal/check-in-pass" in res3.headers["Location"]
