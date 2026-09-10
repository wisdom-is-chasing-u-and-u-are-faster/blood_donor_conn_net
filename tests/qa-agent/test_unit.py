"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-26T13:11:15.586111Z
"""
import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key-for-sessions"
    with app.test_client() as c:
        yield c

def test_find_spatial_candidates(client):
    """Verify spatial matching logic finds candidates within a given radius.

    test_id: cloned_repo__unit__001
    target: find_spatial_candidates
    requirement_id: BO-2
    ac_ids: BO-2-AC-1
    """
    mock_candidates = [
        {"name": "Marcus Vance", "distance_km": 1.2},
        {"name": "Jane Smith", "distance_km": 2.5}
    ]
    with patch("app.spatial_cache.geosearch") as mock_geosearch:
        mock_geosearch.return_value = mock_candidates
        response = client.get("/v1/spatial/candidates?latitude=37.78&longitude=-122.41&radius_km=5")

        assert response.status_code == 200
        data = response.get_json()
        assert data["count"] == 2
        assert data["candidates"] == mock_candidates
        mock_geosearch.assert_called_once_with(
            center_lat=37.78,
            center_lon=-122.41,
            radius_km=5.0,
            abo_type=None,
            rh_factor=None,
            rare_antigen=None
        )

def test_get_donor_eligibility_eligible(client, monkeypatch):
    """Check donor eligibility for whole blood donation when eligible.

    test_id: cloned_repo__unit__002
    target: get_donor_eligibility
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-1
    """
    eligible_date = (datetime.utcnow() - timedelta(days=60)).strftime("%Y-%m-%d")
    mock_donors = [{"username": "eligible_donor", "last_donation": eligible_date}]
    monkeypatch.setattr("app.donors", mock_donors)

    response = client.get("/v1/donors/eligible_donor/eligibility?donation_type=WHOLE_BLOOD")

    assert response.status_code == 200
    data = response.get_json()
    assert data["isEligible"] is True
    assert data["daysRemaining"] == 0

def test_get_donor_eligibility_ineligible(client, monkeypatch):
    """Check donor eligibility for whole blood donation when ineligible.

    test_id: cloned_repo__unit__003_negative_ineligible
    target: get_donor_eligibility
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-1
    """
    ineligible_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    mock_donors = [{"username": "ineligible_donor", "last_donation": ineligible_date}]
    monkeypatch.setattr("app.donors", mock_donors)

    response = client.get("/v1/donors/ineligible_donor/eligibility?donation_type=WHOLE_BLOOD")

    assert response.status_code == 200
    data = response.get_json()
    assert data["isEligible"] is False
    assert data["daysRemaining"] > 0

def test_get_donor_eligibility_double_red_cell(client, monkeypatch):
    """Check donor eligibility for double red cell donation.

    test_id: cloned_repo__unit__004
    target: get_donor_eligibility
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-2
    """
    eligible_date = (datetime.utcnow() - timedelta(days=120)).strftime("%Y-%m-%d")
    mock_donors = [{"username": "drc_donor", "last_donation": eligible_date}]
    monkeypatch.setattr("app.donors", mock_donors)

    response = client.get("/v1/donors/drc_donor/eligibility?donation_type=DOUBLE_RED_CELLS")

    assert response.status_code == 200
    data = response.get_json()
    assert data["isEligible"] is True
    assert data["daysRemaining"] == 0

def test_get_donor_eligibility_platelet(client, monkeypatch):
    """Check donor eligibility for platelet donation.

    test_id: cloned_repo__unit__005
    target: get_donor_eligibility
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-3
    """
    eligible_date = (datetime.utcnow() - timedelta(days=10)).strftime("%Y-%m-%d")
    mock_donors = [{"username": "platelet_donor", "last_donation": eligible_date}]
    monkeypatch.setattr("app.donors", mock_donors)

    response = client.get("/v1/donors/platelet_donor/eligibility?donation_type=PLATELETS")

    assert response.status_code == 200
    data = response.get_json()
    assert data["isEligible"] is True
    assert data["daysRemaining"] == 0

def test_export_worm(client):
    """Verify WORM export function prepares data correctly.

    test_id: cloned_repo__unit__006
    target: export_worm
    requirement_id: BR-002,REQ-005
    ac_ids: BR-002-AC-1,REQ-005-AC-3
    """
    mock_logs = [{"log_id": 1, "action": "TEST_ACTION"}]
    mock_export_data = {"export_id": "WORM-ID-123", "record_count": 1}
    with patch("app.audit_ledger.get_logs") as mock_get_logs, \
         patch("app.security_service.create_worm_export") as mock_create_export:
        mock_get_logs.return_value = mock_logs
        mock_create_export.return_value = mock_export_data

        response = client.post("/v1/compliance/worm-export", json={})

        assert response.status_code == 201
        assert response.get_json() == mock_export_data
        mock_get_logs.assert_called_once()
        mock_create_export.assert_called_once()
        assert mock_create_export.call_args[0][1] == mock_logs

def test_create_emergency_dispatch(client):
    """Verify emergency dispatch creation logic.

    test_id: cloned_repo__unit__007
    target: create_emergency_dispatch
    requirement_id: BO-1
    ac_ids: BO-1-AC-1
    """
    dispatch_payload = {
        "hospital_id": "hosp-1",
        "severity": "LEVEL_1_CATASTROPHIC",
        "required_abo": "O",
        "required_rh": "NEGATIVE",
        "units_requested": 4
    }
    mock_dispatch_object = {"dispatch_id": "disp-xyz-123", **dispatch_payload}

    with patch("app.dispatch_engine.create_dispatch") as mock_create, \
         patch("app.dispatch_engine.enqueue_sqs_message") as mock_enqueue, \
         patch("app.dispatch_engine.process_sqs_worker") as mock_process:
        mock_create.return_value = mock_dispatch_object

        response = client.post("/v1/emergency/dispatch", json=dispatch_payload)

        assert response.status_code == 201
        assert response.get_json() == mock_dispatch_object
        mock_create.assert_called_once()
        mock_enqueue.assert_called_once()
        mock_process.assert_called_once()

def test_reconcile_inventory(client):
    """Verify inventory reconciliation logic.

    test_id: cloned_repo__unit__008
    target: reconcile_inventory
    requirement_id: BO-3
    ac_ids: BO-3-AC-1
    """
    mock_expired_list = [{"reservation_id": "res-123", "status": "EXPIRED"}]
    with patch("app.reservation_engine.reconcile_expired_leases") as mock_reconcile:
        mock_reconcile.return_value = mock_expired_list

        response = client.post("/v1/inventory/reconcile")

        assert response.status_code == 200
        data = response.get_json()
        assert data["reconciled_count"] == 1
        assert data["expired"] == mock_expired_list
        mock_reconcile.assert_called_once()
