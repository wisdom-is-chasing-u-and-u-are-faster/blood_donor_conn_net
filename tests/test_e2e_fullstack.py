"""
Full-Stack End-to-End Smoke & Integration Test Suite (ARCH-1174, ARCH-1183, ARCH-1187, ARCH-1198)
Verifies REST API wiring, static mounting, live endpoints, and multi-tier journeys.
"""
import pytest
from app import app, reservation_engine
from services.audit_service import audit_ledger


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_donor_eligibility_rest_endpoint(client):
    # Test Marcus Vance eligibility check via REST endpoint
    resp = client.get("/v1/donors/marcus_vance/eligibility?donation_type=WHOLE_BLOOD&target_date=2025-02-18")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["isEligible"] is False
    assert data["blockReason"] == "MINIMUM_DONATION_INTERVAL_NOT_MET"

    # Cleared on day 56
    resp_cleared = client.get("/v1/donors/marcus_vance/eligibility?donation_type=WHOLE_BLOOD&target_date=2025-02-19")
    assert resp_cleared.status_code == 200
    assert resp_cleared.get_json()["isEligible"] is True


def test_inventory_reservation_and_reconciliation_flow(client):
    # Reserve unit
    res_payload = {
        "hospital_id": "hosp-1",
        "clinical_encounter_id": "ENC-TRAUMA-9912",
        "din_number": "W036525000101"
    }
    resp = client.post("/v1/inventory/reserve", json=res_payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["success"] is True
    assert data["reservation"]["status"] == "ACTIVE"

    # Reconcile leases endpoint
    reconcile_resp = client.post("/v1/inventory/reconcile")
    assert reconcile_resp.status_code == 200


def test_spatial_proximity_candidates_endpoint(client):
    resp = client.get("/v1/spatial/candidates?latitude=37.7749&longitude=-122.4194&radius_km=15.0")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "candidates" in data
    assert len(data["candidates"]) >= 2


def test_emergency_dispatch_and_status_transition_endpoint(client):
    disp_payload = {
        "hospital_id": "hosp-1",
        "severity": "LEVEL_1_CATASTROPHIC",
        "required_abo": "O",
        "required_rh": "NEGATIVE",
        "units_requested": 4
    }
    resp = client.post("/v1/emergency/dispatch", json=disp_payload)
    assert resp.status_code == 201
    disp_id = resp.get_json()["dispatch_id"]

    # Transition to MATCHING
    status_resp = client.put(f"/v1/emergency/dispatch/{disp_id}/status", json={"status": "MATCHING"})
    assert status_resp.status_code == 200
    assert status_resp.get_json()["status"] == "MATCHING"


def test_audit_integrity_and_worm_export_endpoint(client):
    # Verify audit ledger
    verify_resp = client.get("/v1/audit/verify")
    assert verify_resp.status_code == 200
    assert "is_intact" in verify_resp.get_json()

    # WORM export
    worm_resp = client.post("/v1/compliance/worm-export", json={"export_id": "TEST-WORM-01"})
    assert worm_resp.status_code == 201
    assert worm_resp.get_json()["is_locked"] is True

    # Verify WORM
    check_worm = client.get("/v1/compliance/worm-export/TEST-WORM-01/verify")
    assert check_worm.status_code == 200
    assert check_worm.get_json()["is_valid"] is True


def test_frontend_dashboard_and_command_center_routes(client):
    # Login as hospital
    client.post("/login/hospital", data={"username": "Mercy Hospital", "password": "123"})

    # Hospital dashboard view
    dash_resp = client.get("/hospital/dashboard")
    assert dash_resp.status_code == 200
    assert b"Blood Bank Expiration" in dash_resp.data

    # Dispatch command center view
    cmd_resp = client.get("/dispatch/command-center")
    assert cmd_resp.status_code == 200
    assert b"Clinician Active Dispatch Command Center" in cmd_resp.data
