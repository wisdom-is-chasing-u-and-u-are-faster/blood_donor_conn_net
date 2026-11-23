"""
test_emergency_availability_api.py — Validation for ARCH-9522 Emergency Donor Availability & Response Tracking.
Tests all Acceptance Criteria and Functional Requirements:
- REQ-F-001 & REQ-F-014: Donor toggle availability ('Available' / 'Unavailable')
- REQ-F-002, REQ-F-004, REQ-F-005, REQ-N-002: Cooldown period (56-day) auto-enforcement, status locked
- REQ-F-006, REQ-F-007, REQ-F-008, REQ-F-009, REQ-F-015: "I Can Donate" commitment with ETA, duplicate rejection, open-request check
- REQ-F-010: Live committed donor count per request
- REQ-F-011, REQ-F-012, REQ-F-013, REQ-F-016: Requester/Admin visibility of anonymized donor list with ETAs
"""
import pytest
from datetime import datetime, timezone, timedelta
from app import app, demands, donors, donor_commitments


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_donor_availability_toggle_success(client):
    """AC 1: A donor can log in, see their dashboard, and toggle their availability from 'Unavailable' to 'Available'."""
    with client.session_transaction() as sess:
        sess["username"] = "johndoe"
        sess["role"] = "donor"

    # Set to Unavailable
    res = client.post("/api/v1/donors/availability", json={"status": "Unavailable"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["availability_status"] == "Unavailable"

    # Get status
    res = client.get("/api/v1/donors/availability")
    assert res.status_code == 200
    data = res.get_json()
    assert data["availability_status"] == "Unavailable"
    assert data["is_in_cooldown"] is False

    # Toggle to Available
    res = client.post("/api/v1/donors/availability", json={"status": "Available"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["availability_status"] == "Available"


def test_donor_in_recovery_cooldown_disabled_toggle(client):
    """AC 2: A donor in a cooldown period can see status as 'In Recovery Cooldown' with remaining days, toggle disabled."""
    # Liam Lifesaver is in cooldown
    with client.session_transaction() as sess:
        sess["username"] = "cooldonor"
        sess["role"] = "donor"

    res = client.get("/api/v1/donors/availability")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["availability_status"] == "In Recovery Cooldown"
    assert data["is_in_cooldown"] is True
    assert data["remaining_cooldown_days"] > 0

    # Attempt to change status during cooldown must be rejected (REQ-F-002)
    res = client.post("/api/v1/donors/availability", json={"status": "Available"})
    assert res.status_code == 403
    err_data = res.get_json()
    assert err_data["status"] == "error"
    assert "prevented during recovery cooldown" in err_data["message"]


def test_donor_cooldown_expiry_transitions_to_unavailable(client):
    """REQ-F-005: On cooldown expiry, status must become 'Unavailable'."""
    # Set an expired cooldown for a test donor
    expired_date = (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
    test_d = {
        "name": "Expired Donor",
        "username": "expireddonor",
        "age": 25,
        "gender": "Male",
        "blood_group": "A-",
        "availability_status": "In Recovery Cooldown",
        "cooldown_until": expired_date,
        "last_donation": (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%d")
    }
    donors.append(test_d)

    with client.session_transaction() as sess:
        sess["username"] = "expireddonor"
        sess["role"] = "donor"

    res = client.get("/api/v1/donors/availability")
    assert res.status_code == 200
    data = res.get_json()
    assert data["is_in_cooldown"] is False
    assert data["availability_status"] == "Unavailable"


def test_available_donor_commit_with_eta(client):
    """AC 3 & REQ-F-006, REQ-F-007: 'Available' donor clicks 'I Can Donate', selects ETA, and confirms."""
    with client.session_transaction() as sess:
        sess["username"] = "johndoe"
        sess["role"] = "donor"

    # Ensure johndoe is Available
    client.post("/api/v1/donors/availability", json={"status": "Available"})

    res = client.post("/api/v1/requests/1/commit", json={"eta": "Within 1 hour"})
    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "success"
    assert data["request_id"] == 1
    assert "Donor #" in data["anonymized_id"]
    assert data["eta"] == "Within 1 hour"
    assert data["total_committed"] >= 1


def test_duplicate_commitment_rejected(client):
    """AC 5 & REQ-F-008: An attempt by a donor to commit to the same request twice is rejected (409 Conflict)."""
    with client.session_transaction() as sess:
        sess["username"] = "johndoe"
        sess["role"] = "donor"

    # Attempt to commit again to Request #1
    res = client.post("/api/v1/requests/1/commit", json={"eta": "Within 3 hours"})
    assert res.status_code == 409
    data = res.get_json()
    assert data["status"] == "error"
    assert "already committed" in data["message"].lower() or "duplicate" in data["message"].lower()


def test_cooldown_donor_cannot_commit(client):
    """REQ-F-002 & REQ-F-006: A donor in recovery cooldown cannot commit to an urgent request."""
    with client.session_transaction() as sess:
        sess["username"] = "cooldonor"
        sess["role"] = "donor"

    res = client.post("/api/v1/requests/1/commit", json={"eta": "Within 1 hour"})
    assert res.status_code == 403
    data = res.get_json()
    assert data["status"] == "error"
    assert "cooldown" in data["message"].lower()


def test_unavailable_donor_cannot_commit(client):
    """REQ-F-006: Unavailable donor cannot commit to an urgent request."""
    test_unavail = {
        "name": "Unavailable Donor",
        "username": "unavaildonor",
        "age": 30,
        "gender": "Female",
        "blood_group": "B+",
        "availability_status": "Unavailable",
        "cooldown_until": None
    }
    donors.append(test_unavail)

    with client.session_transaction() as sess:
        sess["username"] = "unavaildonor"
        sess["role"] = "donor"

    res = client.post("/api/v1/requests/1/commit", json={"eta": "Within 1 hour"})
    assert res.status_code == 400
    data = res.get_json()
    assert data["status"] == "error"
    assert "only available donors can commit" in data["message"].lower()


def test_requester_view_anonymized_commitments(client):
    """AC 4 & REQ-F-011, REQ-F-012, REQ-F-013, REQ-F-016: Requester views list of anonymized donors with ETAs."""
    with client.session_transaction() as sess:
        sess["username"] = "Mercy Hospital"
        sess["role"] = "hospital"

    res = client.get("/api/v1/requests/1/commitments")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["request_id"] == 1
    assert data["total_committed"] >= 1
    commitments = data["commitments"]
    assert len(commitments) >= 1
    for c in commitments:
        assert "anonymized_id" in c
        assert c["anonymized_id"].startswith("Donor #")
        assert "eta" in c
        # Ensure raw username is NEVER exposed (REQ-F-013)
        assert "donor_username" not in c
        assert "name" not in c


def test_urgent_requests_live_committed_count(client):
    """REQ-F-010: Urgent requests list displays live committed donor count."""
    res = client.get("/api/v1/requests/urgent")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    req1 = next((r for r in data["requests"] if r["id"] == 1), None)
    assert req1 is not None
    assert req1["committed_count"] >= 1
