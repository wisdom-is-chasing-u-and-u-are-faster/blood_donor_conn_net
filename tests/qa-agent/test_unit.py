"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-24T17:34:01.391219Z
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app import app
from services.eligibility_service import fn_validate_donor_eligibility
from services.reservation_service import reservation_engine
from services.audit_service import AuditLedger
from services.security_service import SecurityService


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as c:
        yield c


def test_find_spatial_candidates_logic(client):
    """Verify spatial candidate logic finds donors within radius.

    test_id: cloned_repo__unit__001
    target: find_spatial_candidates
    requirement_id: BO-2
    ac_ids: BO-2-AC-1
    """
    mock_candidates = [
        {"name": "Donor A", "distance_km": 5.5},
        {"name": "Donor B", "distance_km": 10.1}
    ]
    with patch('app.spatial_cache.geosearch') as mock_geosearch:
        mock_geosearch.return_value = mock_candidates
        response = client.get('/v1/spatial/candidates?latitude=37.7&longitude=-122.4&radius_km=15')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 2
        assert data['candidates'] == mock_candidates
        mock_geosearch.assert_called_once_with(
            center_lat=37.7,
            center_lon=-122.4,
            radius_km=15.0,
            abo_type=None,
            rh_factor=None,
            rare_antigen=None
        )

def test_reconcile_inventory_updates_stock(client):
    """Verify inventory reconciliation logic correctly updates stock levels.

    test_id: cloned_repo__unit__002
    target: reconcile_inventory
    requirement_id: BO-3
    ac_ids: BO-3-AC-1
    """
    mock_expired = [{"reservation_id": "res-123"}]
    with patch('app.reservation_engine.reconcile_expired_leases') as mock_reconcile:
        mock_reconcile.return_value = mock_expired
        response = client.post('/v1/inventory/reconcile')

        assert response.status_code == 200
        data = response.get_json()
        assert data['reconciled_count'] == 1
        assert data['expired'] == mock_expired
        mock_reconcile.assert_called_once()

def test_create_emergency_dispatch_logic(client):
    """Verify emergency dispatch creation logic.

    test_id: cloned_repo__unit__003
    target: create_emergency_dispatch
    requirement_id: BO-1,BO-4
    ac_ids: BO-1-AC-1,BO-4-AC-1
    """
    mock_dispatch = {"dispatch_id": "disp-123", "status": "INITIATED"}
    with patch('app.dispatch_engine.create_dispatch') as mock_create, \
         patch('app.dispatch_engine.enqueue_sqs_message') as mock_enqueue, \
         patch('app.dispatch_engine.process_sqs_worker') as mock_process:
        
        mock_create.return_value = mock_dispatch
        
        response = client.post('/v1/emergency/dispatch', json={
            "hospital_id": "hosp-1",
            "severity": "LEVEL_1_CATASTROPHIC",
            "required_abo": "O",
            "required_rh": "NEGATIVE",
            "units_requested": 2
        })

        assert response.status_code == 201
        assert response.get_json() == mock_dispatch
        mock_create.assert_called_once()
        mock_enqueue.assert_called_once()
        mock_process.assert_called_once()

def test_donor_eligibility_check_for_intervals():
    """Verify donor eligibility check logic for donation intervals.

    test_id: cloned_repo__unit__004
    target: get_donor_eligibility
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-1,REQ-002-AC-2,REQ-002-AC-3
    """
    mock_donor = {"donor_id": "d-1", "is_deferred": False}
    today = datetime(2024, 7, 24)

    # Scenario 1: Whole blood 50 days ago (ineligible)
    history_wb = [{"donation_type": "WHOLE_BLOOD", "collected_at": today - timedelta(days=50)}]
    result_wb = fn_validate_donor_eligibility(mock_donor, history_wb, "WHOLE_BLOOD", target_date=today)
    assert result_wb['isEligible'] is False
    assert result_wb['daysRemaining'] == 6

    # Scenario 2: Double red cells 120 days ago (eligible)
    history_drc = [{"donation_type": "DOUBLE_RED_CELLS", "collected_at": today - timedelta(days=120)}]
    result_drc = fn_validate_donor_eligibility(mock_donor, history_drc, "DOUBLE_RED_CELLS", target_date=today)
    assert result_drc['isEligible'] is True

    # Scenario 3: Platelets 6 days ago (ineligible)
    history_plt = [{"donation_type": "PLATELETS", "collected_at": today - timedelta(days=6)}]
    result_plt = fn_validate_donor_eligibility(mock_donor, history_plt, "PLATELETS", target_date=today)
    assert result_plt['isEligible'] is False
    assert result_plt['daysRemaining'] == 1

def test_inventory_reservation_logic():
    """Verify inventory reservation logic.

    test_id: cloned_repo__unit__005
    target: reserve_inventory
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-4
    """
    # Using the actual engine, but controlling inputs
    reservation_engine.seed_item("DIN-TEST-005", "RED_BLOOD_CELLS", "O", "NEGATIVE", "hosp-test")
    mock_now = datetime(2024, 1, 1, 12, 0, 0)
    expected_expiry = mock_now + timedelta(minutes=120)

    with patch('services.reservation_service.audit_ledger') as mock_audit:
        success, reservation, err = reservation_engine.create_reservation(
            hospital_id="hosp-test",
            clinical_encounter_id="C-TEST-005",
            din_number="DIN-TEST-005",
            reserved_at=mock_now
        )

        assert success is True
        assert err is None
        assert reservation is not None
        assert reservation['expires_at'] == expected_expiry.strftime("%Y-%m-%dT%H:%M:%SZ")
        mock_audit.record_mutation.assert_called_once()

def test_audit_trail_verification_logic(client):
    """Verify audit trail verification logic.

    test_id: cloned_repo__unit__006
    target: verify_audit_trail
    requirement_id: REQ-004
    ac_ids: REQ-004-AC-3
    """
    # Test valid case
    with patch('app.audit_ledger.verify_integrity') as mock_verify:
        mock_verify.return_value = (True, None)
        response = client.get('/v1/audit/verify')
        assert response.status_code == 200
        assert response.get_json()['is_intact'] is True

    # Test invalid case
    with patch('app.audit_ledger.verify_integrity') as mock_verify:
        mock_verify.return_value = (False, "TAMPER_DETECTED")
        response = client.get('/v1/audit/verify')
        assert response.status_code == 200
        data = response.get_json()
        assert data['is_intact'] is False
        assert data['error'] == "TAMPER_DETECTED"

def test_compliance_data_export_logic(client):
    """Verify compliance data export logic.

    test_id: cloned_repo__unit__007
    target: export_worm
    requirement_id: REQ-004
    ac_ids: REQ-004-AC-7,REQ-004-AC-8
    """
    mock_export_data = {"export_id": "WORM-123", "record_count": 5}
    with patch('app.security_service.create_worm_export') as mock_create_worm, \
         patch('app.audit_ledger.get_logs') as mock_get_logs:
        mock_get_logs.return_value = [{"log": "data"}]
        mock_create_worm.return_value = mock_export_data

        response = client.post('/v1/compliance/worm-export', json={"export_id": "WORM-123"})

        assert response.status_code == 201
        assert response.get_json() == mock_export_data
        mock_create_worm.assert_called_once()

def test_hospital_login_authentication_logic(client):
    """Verify hospital login authentication logic.

    test_id: cloned_repo__unit__008
    target: login_hospital
    requirement_id: REQ-004
    ac_ids: REQ-004-AC-1
    """
    # Test successful login
    response_success = client.post('/login/hospital', data={'username': 'testhospital', 'password': 'password'})
    assert response_success.status_code == 302
    assert response_success.location == '/hospital/dashboard'

    # Test failed login
    response_fail = client.post('/login/hospital', data={'username': 'testhospital', 'password': ''})
    assert response_fail.status_code == 200
    assert b'Invalid credentials' in response_fail.data

def test_admin_queue_access_control_logic(client):
    """Verify admin queue access control logic.

    test_id: cloned_repo__unit__009
    target: admin_queue
    requirement_id: REQ-004
    ac_ids: REQ-004-AC-2
    """
    # Test with admin role
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
    response_admin = client.get('/admin/queue')
    assert response_admin.status_code == 200
    assert b'Verification Queue' in response_admin.data

    # Test without admin role (as non-admin user)
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
    response_non_admin = client.get('/admin/queue')
    assert response_non_admin.status_code == 302
    assert response_non_admin.location == '/login/admin'

    # Test without any role (logged out)
    response_logged_out = client.get('/admin/queue')
    assert response_logged_out.status_code == 302
    assert response_logged_out.location == '/login/admin'
