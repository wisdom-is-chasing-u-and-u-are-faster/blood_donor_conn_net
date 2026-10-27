"""Generated API tests for cloned_repo."""
import pytest
from app import app, reservation_engine


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_cloned_repo_api_001(client):
    """
    test_id: cloned_repo__api__001
    target: GET /v1/donors/<donor_id>/eligibility
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-1
    """
    resp_ok = client.get(
        "/v1/donors/marcus_vance/eligibility?donation_type=WHOLE_BLOOD&target_date=2025-06-01"
    )
    assert resp_ok.status_code == 200
    data_ok = resp_ok.get_json()
    assert data_ok["isEligible"] is True

    resp_cd = client.get(
        "/v1/donors/janesmith/eligibility?donation_type=WHOLE_BLOOD&target_date=2025-11-25"
    )
    assert resp_cd.status_code == 200
    data_cd = resp_cd.get_json()
    assert data_cd["isEligible"] is False
    assert data_cd["blockReason"] == "MINIMUM_DONATION_INTERVAL_NOT_MET"


def test_cloned_repo_api_002(client):
    """
    test_id: cloned_repo__api__002
    target: GET /v1/spatial/candidates
    requirement_id: BO-2, BO-4, NFR-PERF-01
    ac_ids: BO-2-AC-1, BO-2-AC-2, BO-4-AC-1, NFR-PERF-01-AC-1
    """
    resp = client.get(
        "/v1/spatial/candidates?latitude=37.7749&longitude=-122.4194&radius_km=25&abo_type=O&rh_factor=NEGATIVE&rare_antigen=kell"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] >= 1
    assert isinstance(data["candidates"], list)
    assert data["candidates"][0]["abo_type"] == "O"


def test_cloned_repo_api_003(client):
    """
    test_id: cloned_repo__api__003
    target: POST /v1/emergency/dispatch
    requirement_id: BO-1
    ac_ids: BO-1-AC-1
    """
    resp = client.post(
        "/v1/emergency/dispatch",
        json={
            "hospital_id": "HOSP-001",
            "severity": "LEVEL_1_CATASTROPHIC",
            "required_abo": "O",
            "required_rh": "NEGATIVE",
            "units_requested": 2,
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["status"] == "INITIATED"
    assert data["hospital_id"] == "HOSP-001"


def test_cloned_repo_api_004(client):
    """
    test_id: cloned_repo__api__004
    target: POST /v1/inventory/reserve
    requirement_id: BR-003
    ac_ids: BR-003-AC-1, BR-003-AC-3
    """
    reservation_engine.seed_item("W036525009901", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
    resp = client.post(
        "/v1/inventory/reserve",
        json={
            "hospital_id": "hosp-1",
            "din_number": "W036525009901",
            "clinical_encounter_id": "ENC-API-9901",
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["success"] is True
    assert data["reservation"]["din_number"] == "W036525009901"

    resp_rec = client.post("/v1/inventory/reconcile")
    assert resp_rec.status_code == 200
    assert "reconciled_count" in resp_rec.get_json()


def test_cloned_repo_api_004_negative_invalid_payload(client):
    """
    test_id: cloned_repo__api__004_negative_invalid_payload
    target: POST /v1/inventory/reserve
    requirement_id: BR-003
    ac_ids: BR-003-AC-2
    """
    resp = client.post(
        "/v1/inventory/reserve",
        json={
            "hospital_id": "hosp-1",
            "din_number": "NON-EXISTENT-DIN",
            "clinical_encounter_id": "ENC-API-FAIL",
        },
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "error" in data


def test_cloned_repo_api_005(client):
    """
    test_id: cloned_repo__api__005
    target: POST /v1/inventory/scan
    requirement_id: BO-3
    ac_ids: BO-3-AC-1, BO-3-AC-2
    """
    resp = client.post("/v1/inventory/scan", json={"barcode": "=W03652500010100"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["parsed"]["din_number"] == "W036525000101"

    resp_worm = client.post("/v1/compliance/worm-export", json={"export_id": "EXP-API-1"})
    assert resp_worm.status_code == 201
    resp_ver = client.get("/v1/compliance/worm-export/EXP-API-1/verify")
    assert resp_ver.status_code == 200
    assert resp_ver.get_json()["is_valid"] is True


def test_cloned_repo_api_006(client):
    """
    test_id: cloned_repo__api__006
    target: GET /v1/audit/verify
    requirement_id: BR-002
    ac_ids: BR-002-AC-1
    """
    resp = client.get("/v1/audit/verify")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_intact"] is True
    assert data["record_count"] >= 1


def test_cloned_repo_api_007(client):
    """
    test_id: cloned_repo__api__007
    target: GET /hospital/dashboard
    requirement_id: BR-001, REQ-002
    ac_ids: BR-001-AC-1, BR-001-AC-2, REQ-002-AC-1
    """
    unauth = client.get("/admin/queue", follow_redirects=False)
    assert unauth.status_code == 302
    assert "/login/admin" in unauth.headers.get("Location", "")

    login = client.post(
        "/login/hospital",
        data={"username": "hosp1", "password": "pw"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    dash = client.get("/hospital/dashboard")
    assert dash.status_code == 200


def test_cloned_repo_api_008(client):
    """
    test_id: cloned_repo__api__008
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    resp = client.post(
        "/login/hospital",
        data={"username": "dr_lin", "password": "secret"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/hospital/dashboard" in resp.headers.get("Location", "")

    logout = client.get("/logout", follow_redirects=False)
    assert logout.status_code == 302
