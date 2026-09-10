"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2024-05-22T13:45:01.123456Z
"""

import pytest
import io
from unittest.mock import patch

from app import app

@pytest.fixture
def client():
    """A test client for the app."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key-for-session'
    with app.test_client() as client:
        yield client

def test_get_donor_eligibility_for_a_valid_donor(client):
    """GET /v1/donors/<donor_id>/eligibility returns eligibility for a valid donor.

    test_id: cloned_repo__api__001
    target: GET /v1/donors/<donor_id>/eligibility
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-1
    """
    with patch('app.fn_validate_donor_eligibility') as mock_validate:
        mock_validate.return_value = {"isEligible": True}
        response = client.get('/v1/donors/donor123/eligibility', headers={'Authorization': 'Bearer valid_token'})

        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data['isEligible'] is True

def test_get_donor_eligibility_returns_ineligibility_for_a_recent_donor(client):
    """GET /v1/donors/<donor_id>/eligibility returns ineligibility for a recent donor.

    test_id: cloned_repo__api__002_negative_ineligible
    target: GET /v1/donors/<donor_id>/eligibility
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-1
    """
    with patch('app.fn_validate_donor_eligibility') as mock_validate:
        mock_validate.return_value = {"isEligible": False}
        response = client.get('/v1/donors/donor456/eligibility', headers={'Authorization': 'Bearer valid_token'})

        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data['isEligible'] is False

def test_get_donor_eligibility_returns_401_without_a_valid_token(client):
    """GET /v1/donors/<donor_id>/eligibility returns 401 without a valid token.

    test_id: cloned_repo__api__003_negative_unauthorized
    target: GET /v1/donors/<donor_id>/eligibility
    requirement_id: REQ-004
    ac_ids: REQ-004-AC-5
    """
    # This test asserts the required security behavior (401 Unauthorized) as per the
    # acceptance criteria. The current application code may not implement this,
    # in which case this test is expected to fail, correctly indicating a gap in
    # meeting the requirement.
    response = client.get('/v1/donors/any_donor_id/eligibility')
    assert response.status_code == 401

def test_get_spatial_candidates_returns_a_list_of_nearby_donors(client):
    """GET /v1/spatial/candidates returns a list of nearby donors.

    test_id: cloned_repo__api__004
    target: GET /v1/spatial/candidates
    requirement_id: BO-2
    ac_ids: BO-2-AC-1
    """
    with patch('app.spatial_cache.geosearch') as mock_geosearch:
        mock_geosearch.return_value = [
            {"member_id": "donor1", "distance_km": 5.0}
        ]
        response = client.get('/v1/spatial/candidates?lat=40.7128&lon=-74.0060&radius=15', headers={'Authorization': 'Bearer valid_token'})

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'candidates' in data
        assert isinstance(data['candidates'], list)

def test_reserve_inventory_successfully_reserves_an_item(client):
    """POST /v1/inventory/reserve successfully reserves an item.

    test_id: cloned_repo__api__005
    target: POST /v1/inventory/reserve
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-2
    """
    with patch('app.reservation_engine.create_reservation') as mock_create:
        mock_create.return_value = (True, {'reservation_id': 'res-123'}, None)
        payload = {'din_number': 'item-abc', 'hospital_id': 'hospital-xyz'}
        response = client.post('/v1/inventory/reserve', json=payload, headers={'Authorization': 'Bearer valid_token'})

        assert response.status_code == 201
        data = response.get_json()
        assert 'reservation' in data
        assert 'reservation_id' in data['reservation']

def test_create_emergency_dispatch_successfully_creates_a_dispatch(client):
    """POST /v1/emergency/dispatch successfully creates a dispatch.

    test_id: cloned_repo__api__006
    target: POST /v1/emergency/dispatch
    requirement_id: BO-4
    ac_ids: BO-4-AC-1
    """
    with patch('app.dispatch_engine.create_dispatch') as mock_create:
        mock_create.return_value = {'dispatch_id': 'disp-xyz'}
        payload = {'blood_type': 'AB-', 'quantity': 2, 'destination': 'hospital-xyz'}
        response = client.post('/v1/emergency/dispatch', json=payload, headers={'Authorization': 'Bearer valid_token'})

        assert response.status_code == 201
        data = response.get_json()
        assert 'dispatch_id' in data

def test_verify_audit_log_confirms_integrity_of_the_audit_log(client):
    """GET /v1/audit/verify confirms integrity of the audit log.

    test_id: cloned_repo__api__007
    target: GET /v1/audit/verify
    requirement_id: REQ-004
    ac_ids: REQ-004-AC-2
    """
    with patch('app.audit_ledger.verify_integrity') as mock_verify:
        mock_verify.return_value = (True, None)
        response = client.get('/v1/audit/verify', headers={'Authorization': 'Bearer admin_token'})

        assert response.status_code == 200
        data = response.get_json()
        assert data['is_intact'] is True

def test_reconcile_inventory_returns_a_successful_response(client):
    """POST /v1/inventory/reconcile returns a successful response.

    test_id: cloned_repo__api__008
    target: POST /v1/inventory/reconcile
    requirement_id: BO-3
    ac_ids: BO-3-AC-1
    """
    with patch('app.reservation_engine.reconcile_expired_leases') as mock_reconcile:
        mock_reconcile.return_value = [{'id': 'res-1'}, {'id': 'res-2'}]
        response = client.post('/v1/inventory/reconcile', headers={'Authorization': 'Bearer admin_token'})

        assert response.status_code == 200
        data = response.get_json()
        assert 'reconciled_count' in data
        assert isinstance(data['expired'], list)

def test_get_hospital_dashboard_returns_200_OK(client):
    """GET /hospital/dashboard returns 200 OK.

    test_id: cloned_repo__api__009_orphan
    target: GET /hospital/dashboard
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
    response = client.get('/hospital/dashboard', headers={'Authorization': 'Bearer hospital_token'})
    assert response.status_code == 200

def test_post_create_demand_returns_200_OK(client):
    """POST /hospital/create-demand returns 200 OK.

    test_id: cloned_repo__api__010_orphan
    target: POST /hospital/create-demand
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'
    
    form_data = {
        'blood_type': 'O+',
        'units': '5',
        'document': (io.BytesIO(b'fake file'), 'test.pdf')
    }
    response = client.post('/hospital/create-demand', data=form_data, content_type='multipart/form-data', headers={'Authorization': 'Bearer hospital_token'})
    
    # The code redirects on success, so we expect a 302 status code.
    assert response.status_code == 302
    assert '/hospital/dashboard' in response.location

def test_get_map_hotspots_returns_200_OK(client):
    """GET /map/hotspots returns 200 OK.

    test_id: cloned_repo__api__011_orphan
    target: GET /map/hotspots
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/map/hotspots')
    assert response.status_code == 200
