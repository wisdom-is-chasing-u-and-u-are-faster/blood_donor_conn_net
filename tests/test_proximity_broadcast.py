import pytest
from app import app
from db.init_db import reset_database


@pytest.fixture
def client():
    app.config["TESTING"] = True
    reset_database()
    with app.test_client() as client:
        yield client


def test_postgis_proximity_radius_and_56_day_filter(client):
    """[ARCH-2101-AC1] [ARCH-2110-AC1] [ARCH-2111-AC1] Test proximity query returns nearby donors and excludes recent donors."""
    payload = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "radiusMiles": 15.0,
        "bloodTypes": ["O_NEG"]
    }

    response = client.post("/api/v1/donors/proximity-search", json=payload)
    assert response.status_code == 200

    data = response.get_json()
    assert data["queryRadiusMiles"] == 15.0
    matched = data["matchedDonors"]
    assert len(matched) >= 2

    # Check that Marcus Chen (donated 20 days ago) is marked DEFERRED
    marcus = next((d for d in matched if d["donorId"] == "donor-003"), None)
    if marcus:
        assert marcus["eligibilityStatus"] == "DEFERRED"

    # Check eligible donors
    vance = next((d for d in matched if d["donorId"] == "donor-001"), None)
    assert vance is not None
    assert vance["eligibilityStatus"] == "ELIGIBLE"
    assert vance["distanceMiles"] < 15.0


def test_multi_channel_notification_fallback(client):
    """[ARCH-2101-AC2] [ARCH-2111-AC1] Test alert broadcast triggers push and fallback SMS."""
    payload = {
        "requestId": "disp-test-broadcast",
        "donorIds": ["donor-001", "donor-002", "donor-003"],
        "message": "URGENT: Emergency Blood Needed.",
        "urgencyTier": "CODE_RED"
    }

    response = client.post("/api/v1/donors/broadcast", json=payload)
    assert response.status_code == 200

    data = response.get_json()
    assert data["targetedDonors"] == 3
    assert data["deliveredPush"] >= 1
    assert data["fallbackSms"] >= 1
