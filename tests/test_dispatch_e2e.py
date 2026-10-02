import pytest
from app import app
from db.init_db import reset_database


@pytest.fixture
def client():
    app.config["TESTING"] = True
    reset_database()
    with app.test_client() as client:
        yield client


def test_code_red_fast_path_execution(client):
    """[ARCH-2100-AC1] [ARCH-2105-AC1] [ARCH-2106-AC1] Test Code Red order creates dispatch and reserves units."""
    payload = {
        "requestingHospitalId": "fac-001",
        "requiredBloodType": "O_NEG",
        "componentType": "RED_BLOOD_CELLS",
        "unitsRequested": 4,
        "urgencyTier": "CODE_RED",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "clinicalNotesEncrypted": "Acute gunshot trauma resuscitation"
    }

    response = client.post("/api/v1/dispatch/emergency-requests", json=payload)
    assert response.status_code == 201

    data = response.get_json()
    assert "requestId" in data
    assert data["status"] == "INVENTORY_ALLOCATED"
    assert data["urgencyTier"] == "CODE_RED"
    assert data["allocatedUnitsCount"] == 4


def test_concurrency_conflict_clean_rejection(client):
    """[ARCH-2100-AC2] [ARCH-2106-AC1] Test insufficient inventory returns HTTP 422 without deadlock."""
    # Only 2 units of B_NEG platelets exist in baseline seed
    # First request consumes both units
    payload1 = {
        "requestingHospitalId": "fac-001",
        "requiredBloodType": "B_NEG",
        "componentType": "PLATELETS",
        "unitsRequested": 2,
        "urgencyTier": "CODE_RED"
    }
    res1 = client.post("/api/v1/dispatch/emergency-requests", json=payload1)
    assert res1.status_code == 201

    # Second competing request for 2 units must receive 422
    payload2 = {
        "requestingHospitalId": "fac-002",
        "requiredBloodType": "B_NEG",
        "componentType": "PLATELETS",
        "unitsRequested": 2,
        "urgencyTier": "CODE_RED"
    }
    res2 = client.post("/api/v1/dispatch/emergency-requests", json=payload2)
    assert res2.status_code == 422

    data2 = res2.get_json()
    assert data2["code"] == "INSUFFICIENT_COMPATIBLE_INVENTORY"


def test_get_dispatch_request_status(client):
    """Test retrieving details and timeline of created dispatch order."""
    payload = {
        "requestingHospitalId": "fac-001",
        "requiredBloodType": "A_POS",
        "componentType": "RED_BLOOD_CELLS",
        "unitsRequested": 1,
        "urgencyTier": "URGENT"
    }
    res = client.post("/api/v1/dispatch/emergency-requests", json=payload)
    assert res.status_code == 201
    req_id = res.get_json()["requestId"]

    details_res = client.get(f"/api/v1/dispatch/emergency-requests/{req_id}")
    assert details_res.status_code == 200
    details = details_res.get_json()
    assert details["requestId"] == req_id
    assert details["requiredBloodType"] == "A_POS"
