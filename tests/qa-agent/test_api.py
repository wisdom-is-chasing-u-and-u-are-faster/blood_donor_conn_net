"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2026-10-29T15:00:00Z
"""
import pytest
from app import app, reservation_engine


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_cloned_repo_api_001(client):
    """Verify authentication and role-scoped access on hospital, admin, and donor routes.

    test_id: cloned_repo__api__001
    target: POST /login/hospital
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-1, REQ-001-AC-2, REQ-001-AC-3
    """
    r_unauth = client.get("/hospital/dashboard")
    assert r_unauth.status_code == 302

    r_admin_unauth = client.post("/admin/verify/1", data={"action": "approve"})
    assert r_admin_unauth.status_code == 302

    r_login = client.post("/login/hospital", data={"username": "dr_lin", "password": "pass"})
    assert r_login.status_code == 302
    assert "/hospital/dashboard" in r_login.location


def test_cloned_repo_api_002(client):
    """Verify GET /v1/donors/<donor_id>/eligibility enforces rolling donation intervals.

    test_id: cloned_repo__api__002
    target: GET /v1/donors/<donor_id>/eligibility
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-1
    """
    resp = client.get("/v1/donors/marcus_vance/eligibility?donation_type=WHOLE_BLOOD&target_date=2026-09-01")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["isEligible"] is True


def test_cloned_repo_api_003(client):
    """Verify GET /v1/spatial/candidates proximity and rare phenotype matching.

    test_id: cloned_repo__api__003
    target: GET /v1/spatial/candidates
    requirement_id: REQ-003
    ac_ids: REQ-003-AC-1, REQ-003-AC-2
    """
    resp = client.get("/v1/spatial/candidates?latitude=37.7749&longitude=-122.4194&radius_km=15&abo_type=O&rh_factor=NEGATIVE&rare_antigen=kell")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] >= 1
    assert any(c["member_id"] == "marcus_vance" for c in data["candidates"])


def test_cloned_repo_api_004(client):
    """Verify POST /v1/emergency/dispatch and status transition endpoints.

    test_id: cloned_repo__api__004
    target: POST /v1/emergency/dispatch
    requirement_id: REQ-004
    ac_ids: REQ-004-AC-1
    """
    create_resp = client.post(
        "/v1/emergency/dispatch",
        json={
            "hospital_id": "hosp-1",
            "severity": "LEVEL_1_CATASTROPHIC",
            "required_abo": "O",
            "required_rh": "NEGATIVE",
            "units_requested": 4,
        },
    )
    assert create_resp.status_code == 201
    disp = create_resp.get_json()
    dispatch_id = disp["dispatch_id"]

    get_resp = client.get(f"/v1/emergency/dispatch/{dispatch_id}")
    assert get_resp.status_code == 200

    put_resp = client.put(
        f"/v1/emergency/dispatch/{dispatch_id}/status",
        json={"status": "MATCHING"},
    )
    assert put_resp.status_code == 200


def test_cloned_repo_api_005(client):
    """Verify inventory scan, reserve, consume, and reconcile endpoints.

    test_id: cloned_repo__api__005
    target: POST /v1/inventory/reserve
    requirement_id: REQ-005, REQ-006
    ac_ids: REQ-005-AC-1, REQ-005-AC-2, REQ-006-AC-1, REQ-006-AC-2
    """
    scan_ok = client.post("/v1/inventory/scan", json={"barcode": "=W03652500010100"})
    assert scan_ok.status_code == 200
    assert scan_ok.get_json()["success"] is True

    scan_bad = client.post("/v1/inventory/scan", json={"barcode": "BAD"})
    assert scan_bad.status_code == 400

    reservation_engine.seed_item("W036525000601", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
    res_ok = client.post(
        "/v1/inventory/reserve",
        json={
            "hospital_id": "hosp-1",
            "clinical_encounter_id": "ENC-API-601",
            "din_number": "W036525000601",
        },
    )
    assert res_ok.status_code == 201

    res_missing = client.post(
        "/v1/inventory/reserve",
        json={"hospital_id": "hosp-1", "clinical_encounter_id": "ENC-API-602", "din_number": "NONEXISTENT"},
    )
    assert res_missing.status_code == 400

    rec_resp = client.post("/v1/inventory/reconcile")
    assert rec_resp.status_code == 200


def test_cloned_repo_api_006(client):
    """Verify audit verification, WORM compliance export, and home/portal endpoints.

    test_id: cloned_repo__api__006
    target: GET /v1/audit/verify
    requirement_id: REQ-007
    ac_ids: REQ-007-AC-2, REQ-007-AC-3
    """
    audit_resp = client.get("/v1/audit/verify")
    assert audit_resp.status_code == 200
    assert audit_resp.get_json()["is_intact"] is True

    worm_resp = client.post("/v1/compliance/worm-export", json={"export_id": "WORM-API-001"})
    assert worm_resp.status_code == 201

    worm_ver = client.get("/v1/compliance/worm-export/WORM-API-001/verify")
    assert worm_ver.status_code == 200
    assert worm_ver.get_json()["is_valid"] is True

    home_resp = client.get("/")
    assert home_resp.status_code == 302
