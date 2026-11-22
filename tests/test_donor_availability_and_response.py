"""
Unit and Integration Tests for ARCH-9275:
Emergency Donor Availability & Response Tracking Feature.
"""
import pytest
from datetime import datetime, timedelta, date
from app import app, donors, demands, donor_commitments, compute_donor_cooldown, anonymize_donor_name


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["DATABASE_PATH"] = None  # in-memory tests
    with app.test_client() as client:
        # Reset state between tests
        donor_commitments.clear()
        for d in donors:
            d["availability_status"] = "Available"
            d["last_donation"] = None
            d["cooldown_until"] = None
        yield client


def test_anonymize_donor_name():
    """Verify donor display name anonymization format (REQ-F-012)."""
    assert anonymize_donor_name("John Doe") == "J. Doe"
    assert anonymize_donor_name("Jane Smith") == "J. Smith"
    assert anonymize_donor_name("Robert") == "R."
    assert anonymize_donor_name("") == "Anonymous Donor"


def test_donor_availability_get_and_toggle(client):
    """
    REQ-F-001, REQ-F-002, REQ-F-003:
    Registered donors can query and toggle availability between 'Available' and 'Unavailable'.
    """
    with client.session_transaction() as sess:
        sess["username"] = "johndoe"
        sess["role"] = "donor"

    # 1. Query initial availability
    res = client.get("/api/v1/donors/availability")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["availability_status"] == "Available"
    assert data["in_cooldown"] is False

    # 2. Toggle to Unavailable
    res = client.post("/api/v1/donors/availability", json={"status": "Unavailable"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["availability_status"] == "Unavailable"

    # Confirm via GET
    res = client.get("/api/v1/donors/availability")
    assert res.get_json()["availability_status"] == "Unavailable"

    # 3. Toggle back to Available
    res = client.post("/api/v1/donors/availability", json={"status": "Available"})
    assert res.status_code == 200
    assert res.get_json()["availability_status"] == "Available"


def test_cooldown_enforcement_and_lockout(client):
    """
    REQ-F-008, REQ-F-009:
    56-day Recovery Cooldown is auto-enforced after donation confirmation,
    preventing the donor from toggling to 'Available' until cooldown ends.
    """
    with client.session_transaction() as sess:
        sess["username"] = "johndoe"
        sess["role"] = "donor"

    # Log a confirmed donation today
    today_str = date.today().strftime("%Y-%m-%d")
    res = client.post("/api/v1/donors/log-donation", json={"username": "johndoe", "donation_date": today_str})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["availability_status"] == "In Recovery Cooldown"
    assert data["cooldown_remaining_days"] == 56

    # Attempt to change status to 'Available' during cooldown -> must be prohibited
    res = client.post("/api/v1/donors/availability", json={"status": "Available"})
    assert res.status_code == 400
    err_data = res.get_json()
    assert err_data["status"] == "error"
    assert "Recovery Cooldown" in err_data["message"]
    assert err_data["cooldown_remaining_days"] == 56

    # Donor can still view status and remaining days
    res = client.get("/api/v1/donors/availability")
    assert res.status_code == 200
    status_data = res.get_json()
    assert status_data["availability_status"] == "In Recovery Cooldown"
    assert status_data["in_cooldown"] is True
    assert status_data["cooldown_remaining_days"] == 56


def test_commitment_by_available_donor_and_tally(client):
    """
    REQ-F-004, REQ-F-007, REQ-F-010:
    Available donor commits 'I Can Donate' with ETA to open request.
    Tally increments accordingly.
    """
    with client.session_transaction() as sess:
        sess["username"] = "johndoe"
        sess["role"] = "donor"

    # Ensure donor is Available
    client.post("/api/v1/donors/availability", json={"status": "Available"})

    # Commit to request #1 with ETA 'within 1 hour'
    res = client.post("/api/v1/requests/1/commitments", json={"eta": "within 1 hour"})
    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "success"
    assert data["committed_donor_count"] == 1

    # Verify tally reflects in GET /api/v1/requests
    res = client.get("/api/v1/requests")
    assert res.status_code == 200
    requests_data = res.get_json()["requests"]
    req1 = next(r for r in requests_data if r["id"] == 1)
    assert req1["committed_donor_count"] == 1
    assert req1["user_committed"] is True


def test_rejection_of_commitment_when_not_available(client):
    """
    REQ-F-005:
    Prevent commitment if donor status is not 'Available' (e.g. Unavailable or Cooldown).
    """
    with client.session_transaction() as sess:
        sess["username"] = "johndoe"
        sess["role"] = "donor"

    # Set status to Unavailable
    client.post("/api/v1/donors/availability", json={"status": "Unavailable"})

    # Attempt to commit
    res = client.post("/api/v1/requests/1/commitments", json={"eta": "today"})
    assert res.status_code == 400
    assert "Unavailable" in res.get_json()["message"]

    # Put donor in Recovery Cooldown
    client.post("/api/v1/donors/log-donation", json={"username": "johndoe"})

    # Attempt to commit again
    res = client.post("/api/v1/requests/1/commitments", json={"eta": "today"})
    assert res.status_code == 400
    assert "Recovery Cooldown" in res.get_json()["message"]


def test_duplicate_commitment_prevention(client):
    """
    REQ-F-006:
    Prevent duplicate commitments from the same donor to the same request.
    """
    with client.session_transaction() as sess:
        sess["username"] = "johndoe"
        sess["role"] = "donor"

    # 1st commitment -> success
    res = client.post("/api/v1/requests/1/commitments", json={"eta": "within 3 hours"})
    assert res.status_code == 201

    # 2nd commitment by same donor to same request -> rejected (HTTP 409 Conflict)
    res = client.post("/api/v1/requests/1/commitments", json={"eta": "within 1 hour"})
    assert res.status_code == 409
    data = res.get_json()
    assert data["status"] == "error"
    assert "already committed" in data["message"].lower()
    assert data["duplicate"] is True


def test_requester_and_admin_visibility_and_rbac(client):
    """
    REQ-F-010, REQ-F-011, REQ-F-012, REQ-F-013:
    Requesters and district admins can view live tallies and anonymized donor roster.
    Hospital requesters are restricted to viewing only their own demands.
    """
    # 1. Donor commits to demand #1 (belonging to 'General Hospital')
    with client.session_transaction() as sess:
        sess["username"] = "johndoe"
        sess["role"] = "donor"
    client.post("/api/v1/requests/1/commitments", json={"eta": "within 1 hour"})

    # 2. District Admin views commitments for demand #1 -> Allowed
    with client.session_transaction() as sess:
        sess["username"] = "district_admin"
        sess["role"] = "admin"
    res = client.get("/api/v1/requests/1/commitments")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["committed_donor_count"] == 1
    commitments = data["commitments"]
    assert len(commitments) == 1
    assert commitments[0]["anonymous_name"] == "J. Doe"
    assert commitments[0]["eta"] == "within 1 hour"

    # 3. Hospital requester from 'General Hospital' views demand #1 -> Allowed
    with client.session_transaction() as sess:
        sess["username"] = "hospital_user"
        sess["role"] = "hospital"
        sess["hospital_name"] = "General Hospital"
    res = client.get("/api/v1/requests/1/commitments")
    assert res.status_code == 200
    assert res.get_json()["committed_donor_count"] == 1

    # 4. Hospital requester from a different hospital views demand #1 -> 403 Forbidden
    with client.session_transaction() as sess:
        sess["username"] = "other_hospital_user"
        sess["role"] = "hospital"
        sess["hospital_name"] = "St. Marys Hospital"
    res = client.get("/api/v1/requests/1/commitments")
    assert res.status_code == 403
    assert "restricted" in res.get_json()["message"].lower()


def test_ui_pages_serving(client):
    """Verify that the self-contained UI pages are mounted and served with HTTP 200."""
    pages = ["donor-dashboard.html", "donor-requests.html", "requester-dashboard.html"]
    for p in pages:
        res = client.get(f"/pages/{p}")
        assert res.status_code == 200
        assert b"api.js" in res.data
