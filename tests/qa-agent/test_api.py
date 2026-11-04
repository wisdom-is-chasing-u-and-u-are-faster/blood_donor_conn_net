"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2026-11-04T14:18:00Z
"""
import pytest
from app import app
from services.reservation_service import reservation_engine


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_cloned_repo_api_001(client):
    """POST /v1/emergency/dispatch creates dispatch and GET /v1/emergency/dispatch/<id> retrieves it.

    test_id: cloned_repo__api__001
    target: POST /v1/emergency/dispatch
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-1
    """
    resp = client.post(
        "/v1/emergency/dispatch",
        json={
            "hospital_id": "hosp-1",
            "severity": "LEVEL_1_CATASTROPHIC",
            "required_abo": "O",
            "required_rh": "NEGATIVE",
            "units_requested": 4
        }
    )
    assert resp.status_code == 201
    data = resp.get_json()
    dispatch_id = data["dispatch_id"]
    assert data["status"] == "INITIATED"

    get_resp = client.get(f"/v1/emergency/dispatch/{dispatch_id}")
    assert get_resp.status_code == 200
    assert get_resp.get_json()["dispatch_id"] == dispatch_id

    put_resp = client.put(
        f"/v1/emergency/dispatch/{dispatch_id}/status",
        json={"status": "MATCHING"}
    )
    assert put_resp.status_code == 200
    assert put_resp.get_json()["status"] == "MATCHING"


def test_cloned_repo_api_001_negative_invalid_status(client):
    """PUT /v1/emergency/dispatch/<id>/status returns 400 on invalid state transition.

    test_id: cloned_repo__api__001_negative_invalid_status
    target: PUT /v1/emergency/dispatch/<dispatch_id>/status
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-1
    """
    resp = client.post(
        "/v1/emergency/dispatch",
        json={"hospital_id": "hosp-1", "required_abo": "O", "required_rh": "NEGATIVE", "units_requested": 2}
    )
    dispatch_id = resp.get_json()["dispatch_id"]

    put_resp = client.put(
        f"/v1/emergency/dispatch/{dispatch_id}/status",
        json={"status": "FULFILLED"}
    )
    assert put_resp.status_code == 400
    assert put_resp.get_json()["success"] is False


def test_cloned_repo_api_002(client):
    """GET /v1/spatial/candidates returns matching donors within 15 km radius.

    test_id: cloned_repo__api__002
    target: GET /v1/spatial/candidates
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-2, REQ-001-AC-3
    """
    resp = client.get(
        "/v1/spatial/candidates?latitude=37.7749&longitude=-122.4194&radius_km=15&abo_type=O&rh_factor=NEGATIVE"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["count"] >= 1
    assert all(c["distance_km"] <= 15.0 for c in body["candidates"])

    resp_rare = client.get(
        "/v1/spatial/candidates?latitude=37.7749&longitude=-122.4194&radius_km=15&rare_antigen=kell"
    )
    assert resp_rare.status_code == 200
    rare_body = resp_rare.get_json()
    assert rare_body["count"] >= 1
    assert any(c["member_id"] == "marcus_vance" for c in rare_body["candidates"])


def test_cloned_repo_api_003(client):
    """GET /v1/donors/<donor_id>/eligibility evaluates rolling donation interval.

    test_id: cloned_repo__api__003
    target: GET /v1/donors/<donor_id>/eligibility
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-1
    """
    resp1 = client.get(
        "/v1/donors/marcus_vance/eligibility?donation_type=WHOLE_BLOOD&target_date=2026-06-01"
    )
    assert resp1.status_code == 200
    assert resp1.get_json()["isEligible"] is True

    resp2 = client.get(
        "/v1/donors/janesmith/eligibility?donation_type=WHOLE_BLOOD&target_date=2025-11-20"
    )
    assert resp2.status_code == 200
    body2 = resp2.get_json()
    assert body2["isEligible"] is False
    assert body2["blockReason"] == "MINIMUM_DONATION_INTERVAL_NOT_MET"


def test_cloned_repo_api_004(client):
    """POST /v1/inventory/reserve, /v1/inventory/consume, and /v1/inventory/reconcile manage inventory leases.

    test_id: cloned_repo__api__004
    target: POST /v1/inventory/reserve
    requirement_id: REQ-003, REQ-005
    ac_ids: REQ-003-AC-1, REQ-005-AC-1
    """
    reservation_engine.seed_item("W036525770001", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
    res_resp = client.post(
        "/v1/inventory/reserve",
        json={
            "hospital_id": "hosp-1",
            "clinical_encounter_id": "ENC-API-01",
            "din_number": "W036525770001"
        }
    )
    assert res_resp.status_code == 201
    res_data = res_resp.get_json()
    assert res_data["success"] is True
    res_id = res_data["reservation"]["reservation_id"]

    con_resp = client.post(
        "/v1/inventory/consume",
        json={"reservation_id": res_id}
    )
    assert con_resp.status_code == 200
    assert con_resp.get_json()["status"] == "CONSUMED"

    rec_resp = client.post(
        "/v1/inventory/reconcile"
    )
    assert rec_resp.status_code == 200
    assert "reconciled_count" in rec_resp.get_json()


def test_cloned_repo_api_004_negative_invalid_reserve(client):
    """POST /v1/inventory/reserve returns 400 for non-existent DIN.

    test_id: cloned_repo__api__004_negative_invalid_reserve
    target: POST /v1/inventory/reserve
    requirement_id: REQ-005
    ac_ids: REQ-005-AC-2
    """
    resp = client.post(
        "/v1/inventory/reserve",
        json={"din_number": "NON_EXISTENT_DIN_999"}
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["success"] is False
    assert body["error"] == "ITEM_NOT_FOUND"


def test_cloned_repo_api_005(client):
    """POST /v1/inventory/scan parses ISBT-128 barcode and rejects invalid barcode.

    test_id: cloned_repo__api__005
    target: POST /v1/inventory/scan
    requirement_id: REQ-003
    ac_ids: REQ-003-AC-2
    """
    resp_ok = client.post(
        "/v1/inventory/scan",
        json={"barcode": "=W03652500010100"}
    )
    assert resp_ok.status_code == 200
    assert resp_ok.get_json()["success"] is True
    assert resp_ok.get_json()["parsed"]["din_number"] == "W036525000101"

    resp_bad = client.post(
        "/v1/inventory/scan",
        json={"barcode": "BAD"}
    )
    assert resp_bad.status_code == 400
    assert resp_bad.get_json()["success"] is False


def test_cloned_repo_api_006(client):
    """Portal login and role-protected routes enforce session authentication and role checks.

    test_id: cloned_repo__api__006
    target: POST /login/hospital
    requirement_id: REQ-004
    ac_ids: REQ-004-AC-1, REQ-004-AC-2
    """
    r_hosp_unauth = client.get("/hospital/dashboard")
    assert r_hosp_unauth.status_code == 302

    r_admin_unauth = client.get("/admin/queue")
    assert r_admin_unauth.status_code == 302

    r_login = client.post(
        "/login/hospital",
        data={"username": "hosp_user", "password": "secret123"}
    )
    assert r_login.status_code == 302

    r_hosp_auth = client.get("/hospital/dashboard")
    assert r_hosp_auth.status_code == 200

    r_admin_forbidden = client.get("/admin/queue")
    assert r_admin_forbidden.status_code == 302


def test_cloned_repo_api_007(client):
    """GET /v1/audit/verify and /v1/compliance/worm-export verify audit ledger and WORM archive.

    test_id: cloned_repo__api__007
    target: GET /v1/audit/verify
    requirement_id: REQ-006
    ac_ids: REQ-006-AC-4
    """
    r_audit = client.get("/v1/audit/verify")
    assert r_audit.status_code == 200
    assert r_audit.get_json()["is_intact"] is True

    r_worm = client.post(
        "/v1/compliance/worm-export",
        json={"export_id": "WORM-TEST-01"}
    )
    assert r_worm.status_code == 201
    assert r_worm.get_json()["is_locked"] is True

    r_verify = client.get("/v1/compliance/worm-export/WORM-TEST-01/verify")
    assert r_verify.status_code == 200
    assert r_verify.get_json()["is_valid"] is True
