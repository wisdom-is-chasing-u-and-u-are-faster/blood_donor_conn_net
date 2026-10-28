"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2026-10-28T14:50:00Z
"""
import pytest
from app import app, reservation_engine


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_cloned_repo_api_001(client):
    """POST /v1/emergency/dispatch creates emergency dispatch within SLA.

    test_id: cloned_repo__api__001
    target: POST /v1/emergency/dispatch
    requirement_id: BO-1
    ac_ids: BO-1-AC-1
    """
    response = client.post("/v1/emergency/dispatch", json={
        "hospital_id": "hosp-1",
        "severity": "LEVEL_1_CATASTROPHIC",
        "required_abo": "O",
        "required_rh": "NEGATIVE",
        "units_requested": 4
    })
    assert response.status_code == 201
    body = response.get_json()
    assert "dispatch_id" in body
    assert body["status"] == "INITIATED"


def test_cloned_repo_api_002(client):
    """PUT /v1/emergency/dispatch/<dispatch_id>/status updates dispatch state.

    test_id: cloned_repo__api__002
    target: PUT /v1/emergency/dispatch/<dispatch_id>/status
    requirement_id: BO-1
    ac_ids: BO-1-AC-2
    """
    created = client.post("/v1/emergency/dispatch", json={"hospital_id": "hosp-1"}).get_json()
    dispatch_id = created["dispatch_id"]
    response = client.put(f"/v1/emergency/dispatch/{dispatch_id}/status", json={"status": "MATCHING"})
    assert response.status_code == 200
    assert response.get_json()["status"] == "MATCHING"
    get_resp = client.get(f"/v1/emergency/dispatch/{dispatch_id}")
    assert get_resp.status_code == 200
    assert get_resp.get_json()["status"] == "MATCHING"


def test_cloned_repo_api_003(client):
    """GET /v1/spatial/candidates returns matching donors within 15 km radius.

    test_id: cloned_repo__api__003
    target: GET /v1/spatial/candidates
    requirement_id: BO-2, BO-4
    ac_ids: BO-2-AC-1, BO-2-AC-2, BO-4-AC-2
    """
    response = client.get("/v1/spatial/candidates?latitude=37.7749&longitude=-122.4194&radius_km=15&abo_type=O&rh_factor=NEGATIVE")
    assert response.status_code == 200
    body = response.get_json()
    assert body["count"] >= 1
    assert isinstance(body["candidates"], list)


def test_cloned_repo_api_004(client):
    """POST /v1/inventory/scan parses ISBT-128 barcode telemetry.

    test_id: cloned_repo__api__004
    target: POST /v1/inventory/scan
    requirement_id: BO-3
    ac_ids: BO-3-AC-1
    """
    response = client.post("/v1/inventory/scan", json={"barcode": "=W03652500010100"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["parsed"]["din_number"] == "W036525000101"


def test_cloned_repo_api_005(client):
    """POST /v1/inventory/reserve reserves inventory with idempotency key.

    test_id: cloned_repo__api__005
    target: POST /v1/inventory/reserve
    requirement_id: BO-3, UC-001
    ac_ids: BO-3-AC-2, UC-001-AC-1
    """
    reservation_engine.seed_item("W036525000888", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
    response = client.post("/v1/inventory/reserve", json={
        "hospital_id": "hosp-1",
        "clinical_encounter_id": "ENC-API-005",
        "din_number": "W036525000888"
    })
    assert response.status_code == 201
    assert response.get_json()["success"] is True
    rec_resp = client.post("/v1/inventory/reconcile")
    assert rec_resp.status_code == 200


def test_cloned_repo_api_005_negative_invalid_payload(client):
    """POST /v1/inventory/reserve rejects missing or non-existent DIN with 400.

    test_id: cloned_repo__api__005_negative_invalid_payload
    target: POST /v1/inventory/reserve
    requirement_id: UC-001
    ac_ids: UC-001-AC-2
    """
    response = client.post("/v1/inventory/reserve", json={"din_number": "NON_EXISTENT_DIN"})
    assert response.status_code == 400
    body = response.get_json()
    assert body["success"] is False
    assert body["error"] == "ITEM_NOT_FOUND"


def test_cloned_repo_api_006(client):
    """GET /v1/donors/<donor_id>/eligibility evaluates rolling donation interval.

    test_id: cloned_repo__api__006
    target: GET /v1/donors/<donor_id>/eligibility
    requirement_id: BO-4
    ac_ids: BO-4-AC-1
    """
    response = client.get("/v1/donors/marcus_vance/eligibility?donation_type=WHOLE_BLOOD")
    assert response.status_code == 200
    body = response.get_json()
    assert "isEligible" in body


def test_cloned_repo_api_007_negative_unauthenticated(client):
    """GET /hospital/dashboard blocks unauthenticated requests.

    test_id: cloned_repo__api__007_negative_unauthenticated
    target: GET /hospital/dashboard
    requirement_id: BR-001
    ac_ids: BR-001-AC-1, BR-001-AC-2
    """
    client.get("/logout")
    resp_dash = client.get("/hospital/dashboard")
    assert resp_dash.status_code == 302
    assert "/login/hospital" in resp_dash.location
    resp_admin = client.post("/admin/verify/1", data={"action": "approve"})
    assert resp_admin.status_code == 302
    assert "/login/admin" in resp_admin.location


def test_cloned_repo_api_008(client):
    """GET /v1/audit/verify and POST /v1/compliance/worm-export verify compliance.

    test_id: cloned_repo__api__008
    target: GET /v1/audit/verify
    requirement_id: BR-002
    ac_ids: BR-002-AC-1, BR-002-AC-2
    """
    audit_resp = client.get("/v1/audit/verify")
    assert audit_resp.status_code == 200
    assert audit_resp.get_json()["is_intact"] is True
    worm_resp = client.post("/v1/compliance/worm-export", json={"export_id": "WORM-API-008"})
    assert worm_resp.status_code == 201
    assert worm_resp.get_json()["export_id"] == "WORM-API-008"


def test_cloned_repo_api_009(client):
    """GET / and portal orphan endpoints respond cleanly.

    test_id: cloned_repo__api__009
    target: GET /
    requirement_id: NFR-PERF-01
    ac_ids: NFR-PERF-01-AC-1
    """
    resp_root = client.get("/")
    assert resp_root.status_code == 302
    assert client.get("/login/hospital").status_code == 200
    assert client.get("/login/donor").status_code == 200
    assert client.get("/login/admin").status_code == 200
    assert client.get("/map/hotspots").status_code == 200
