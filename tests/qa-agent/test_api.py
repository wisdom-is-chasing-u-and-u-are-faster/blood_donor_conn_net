"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2026-10-28T06:38:00Z
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
    """GET /v1/donors/<donor_id>/eligibility returns rolling eligibility status.

    test_id: cloned_repo__api__001
    target: GET /v1/donors/<donor_id>/eligibility
    requirement_id: REQ-001, NFR-PERF-01
    ac_ids: REQ-001-AC-1, NFR-PERF-01-AC-1
    """
    response = client.get("/v1/donors/marcus_vance/eligibility?donation_type=WHOLE_BLOOD")
    assert response.status_code == 200
    data = response.get_json()
    assert "isEligible" in data
    assert "nextEligibleDate" in data


def test_cloned_repo_api_002(client):
    """GET /v1/spatial/candidates returns proximity-matched donors within 15 km and filters rare antigens.

    test_id: cloned_repo__api__002
    target: GET /v1/spatial/candidates
    requirement_id: BO-2, BO-4
    ac_ids: BO-2-AC-1, BO-2-AC-2, BO-4-AC-1
    """
    response = client.get("/v1/spatial/candidates?latitude=37.7749&longitude=-122.4194&radius_km=15&rare_antigen=kell")
    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] >= 1
    assert any(c["member_id"] == "marcus_vance" for c in data["candidates"])


def test_cloned_repo_api_003(client):
    """POST /v1/inventory/reserve creates 120-minute blood unit lease and rejects duplicate reserve.

    test_id: cloned_repo__api__003
    target: POST /v1/inventory/reserve
    requirement_id: BR-003, UC-001
    ac_ids: BR-003-AC-1, UC-001-AC-1
    """
    reservation_engine.seed_item("W036525000401", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-1")
    r1 = client.post("/v1/inventory/reserve", json={"din_number": "W036525000401", "hospital_id": "hosp-1"})
    assert r1.status_code == 201
    assert r1.get_json()["success"] is True

    r2 = client.post("/v1/inventory/reserve", json={"din_number": "W036525000401", "hospital_id": "hosp-1"})
    assert r2.status_code == 400
    assert r2.get_json()["success"] is False


def test_cloned_repo_api_004(client):
    """POST /v1/inventory/reconcile releases expired inventory reservations.

    test_id: cloned_repo__api__004
    target: POST /v1/inventory/reconcile
    requirement_id: BO-3
    ac_ids: BO-3-AC-2
    """
    response = client.post("/v1/inventory/reconcile")
    assert response.status_code == 200
    data = response.get_json()
    assert "reconciled_count" in data
    assert isinstance(data["expired"], list)


def test_cloned_repo_api_005(client):
    """POST /v1/inventory/scan parses valid ISBT-128 barcode and returns 400 on invalid barcode.

    test_id: cloned_repo__api__005
    target: POST /v1/inventory/scan
    requirement_id: BO-3, UC-001
    ac_ids: BO-3-AC-1, UC-001-AC-2
    """
    valid_resp = client.post("/v1/inventory/scan", json={"barcode": "=W03652500010100"})
    assert valid_resp.status_code == 200
    assert valid_resp.get_json()["success"] is True

    invalid_resp = client.post("/v1/inventory/scan", json={"barcode": ""})
    assert invalid_resp.status_code == 400
    assert invalid_resp.get_json()["success"] is False


def test_cloned_repo_api_006(client):
    """POST /v1/emergency/dispatch creates dispatch and GET /v1/emergency/dispatch/<id> returns 404 on unknown ID.

    test_id: cloned_repo__api__006
    target: POST /v1/emergency/dispatch
    requirement_id: BO-1, UC-001, FR-02
    ac_ids: BO-1-AC-1, UC-001-AC-3, FR-02-AC-1
    """
    post_resp = client.post("/v1/emergency/dispatch", json={
        "hospital_id": "hosp-1",
        "severity": "LEVEL_1_CATASTROPHIC",
        "required_abo": "O",
        "required_rh": "NEGATIVE",
        "units_requested": 4
    })
    assert post_resp.status_code == 201
    disp_id = post_resp.get_json()["dispatch_id"]

    put_resp = client.put(f"/v1/emergency/dispatch/{disp_id}/status", json={"status": "MATCHING"})
    assert put_resp.status_code == 200

    not_found_resp = client.get("/v1/emergency/dispatch/nonexistent-dispatch-id")
    assert not_found_resp.status_code == 404
    assert not_found_resp.get_json()["error"] == "NOT_FOUND"


def test_cloned_repo_api_007(client):
    """GET /v1/audit/verify and WORM compliance export endpoints verify tamper-evident logs.

    test_id: cloned_repo__api__007
    target: GET /v1/audit/verify
    requirement_id: BR-002, NFR-SEC-01
    ac_ids: BR-002-AC-1, BR-002-AC-2, NFR-SEC-01-AC-1
    """
    audit_resp = client.get("/v1/audit/verify")
    assert audit_resp.status_code == 200
    assert audit_resp.get_json()["is_intact"] is True

    worm_resp = client.post("/v1/compliance/worm-export", json={"export_id": "WORM-API-01"})
    assert worm_resp.status_code == 201

    verify_resp = client.get("/v1/compliance/worm-export/WORM-API-01/verify")
    assert verify_resp.status_code == 200
    assert verify_resp.get_json()["is_valid"] is True


def test_cloned_repo_api_008(client):
    """Authentication, RBAC role guards, and portal views enforce session access control.

    test_id: cloned_repo__api__008
    target: GET /login/social/<provider>
    requirement_id: BR-001, NFR-PERF-01, UI-001
    ac_ids: BR-001-AC-1, BR-001-AC-2, BR-001-AC-3, NFR-PERF-01-AC-2, UI-001-AC-1
    """
    unauth_profile = client.get("/donor/profile")
    assert unauth_profile.status_code == 302

    unauth_admin = client.post("/admin/verify/1", data={"action": "approve"})
    assert unauth_admin.status_code == 302

    social_resp = client.get("/login/social/google")
    assert social_resp.status_code == 302

    home_resp = client.get("/")
    assert home_resp.status_code == 302

    dash_resp = client.get("/hospital/dashboard")
    assert dash_resp.status_code == 200


def test_cloned_repo_api_009(client):
    """Orphan endpoints smoke verification for login, registration, command center, and hotspots map.

    test_id: cloned_repo__api__009
    target: GET /map/hotspots
    requirement_id: no requirement
    ac_ids: none
    """
    assert client.get("/login/hospital").status_code == 200
    assert client.get("/login/donor").status_code == 200
    assert client.get("/donor/register").status_code == 200
    assert client.get("/dispatch/command-center").status_code == 200
    assert client.get("/map/hotspots").status_code == 200
    assert client.get("/logout").status_code == 302
