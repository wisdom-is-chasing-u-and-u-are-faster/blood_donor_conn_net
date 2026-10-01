"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-25T17:04:18.123456Z
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Import the app for context and the client fixture
from app import app

# Import service layer components for direct unit testing
from services.spatial_service import RedisGeospatialCache
from services.eligibility_service import fn_validate_donor_eligibility
from services.reservation_service import ReservationEngine
from services.security_service import SecurityService
from services.dispatch_service import DispatchStateMachine

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as c:
        yield c

def test_cloned_repo_unit_001_spatial_matching_logic():
    """Verifies spatial matching logic correctly identifies candidate donors.

    test_id: cloned_repo__unit__001
    target: find_spatial_candidates
    requirement_id: BO-2
    ac_ids: BO-2-AC-1
    """
    spatial_cache = RedisGeospatialCache()
    center_lat, center_lon = 37.7749, -122.4194

    # Donor inside the radius
    spatial_cache.geoadd("donor_inside", 37.7800, -122.4100, metadata={"name": "Inside Donor"})
    # Donor outside the radius
    spatial_cache.geoadd("donor_outside", 37.9000, -122.5000, metadata={"name": "Outside Donor"})

    candidates = spatial_cache.geosearch(center_lat, center_lon, radius_km=15.0)

    assert len(candidates) == 1
    assert candidates[0]['member_id'] == "donor_inside"
    assert 'name' in candidates[0]
    assert candidates[0]['name'] == "Inside Donor"

@pytest.mark.parametrize(
    "donation_type, last_donation_days_ago, expected_eligibility",
    [
        ("WHOLE_BLOOD", 30, False), # Ineligible, < 56 days
        ("WHOLE_BLOOD", 60, True),  # Eligible, > 56 days
        ("PLATELETS", 3, False),   # Ineligible, < 7 days
        ("PLATELETS", 8, True),    # Eligible, > 7 days
    ]
)
def test_cloned_repo_unit_002_donor_eligibility_intervals(donation_type, last_donation_days_ago, expected_eligibility):
    """Verifies donor eligibility logic enforces various donation intervals.

    test_id: cloned_repo__unit__002
    target: get_donor_eligibility
    requirement_id: REQ-002
    ac_ids: REQ-002-AC-1, REQ-002-AC-2, REQ-002-AC-3
    """
    mock_donor = {"donor_id": "donor123", "is_deferred": False}
    eval_date = datetime(2024, 7, 25)
    last_donation_date = eval_date - timedelta(days=last_donation_days_ago)

    mock_history = [
        {
            "donation_type": donation_type,
            "collected_at": last_donation_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    ]

    result = fn_validate_donor_eligibility(
        donor=mock_donor,
        donation_history=mock_history,
        donation_type=donation_type,
        target_date=eval_date
    )

    assert result["isEligible"] == expected_eligibility

@patch('services.reservation_service.audit_ledger')
def test_cloned_repo_unit_003_inventory_reservation_auditing(mock_audit_ledger):
    """Verifies inventory reservation creates an audit trail and a 120-minute lease.

    test_id: cloned_repo__unit__003
    target: reserve_inventory
    requirement_id: REQ-003
    ac_ids: REQ-003-AC-1
    """
    engine = ReservationEngine()
    din = "W123456789012"
    engine.seed_item(din, "RED_BLOOD_CELLS", "O", "POSITIVE", "hosp-1")

    reserved_at_time = datetime.utcnow()
    success, reservation, error = engine.create_reservation(
        hospital_id="hosp-1",
        clinical_encounter_id="enc-1",
        din_number=din,
        reserved_by="test_user",
        reserved_at=reserved_at_time
    )

    assert success is True
    assert error is None
    assert reservation is not None
    assert reservation['status'] == 'ACTIVE'

    # Verify the 120-minute lease is set
    expires_at_dt = datetime.strptime(reservation['expires_at'], "%Y-%m-%dT%H:%M:%SZ")
    assert expires_at_dt == reserved_at_time + timedelta(minutes=120)

    # Verify the audit log was called, which replaces the non-existent scheduler call
    mock_audit_ledger.record_mutation.assert_called_once()
    call_args = mock_audit_ledger.record_mutation.call_args[1]
    assert call_args['entity_name'] == 'inventory_reservations'
    assert call_args['action_type'] == 'INSERT'
    assert call_args['new_state'] == reservation

@patch('app.security_service')
@patch('app.audit_ledger')
def test_cloned_repo_unit_004_worm_export_preparation(mock_audit_ledger, mock_security_service, client):
    """Verifies the WORM export function correctly prepares data for compliance.

    test_id: cloned_repo__unit__004
    target: export_worm
    requirement_id: BR-002, REQ-004
    ac_ids: BR-002-AC-1, REQ-004-AC-3, REQ-004-AC-2
    """
    mock_logs = [{'log_id': 1, 'details': 'test log'}]
    mock_export_obj = {'export_id': 'WORM-123', 'sha256_checksum': 'abc'}
    mock_audit_ledger.get_logs.return_value = mock_logs
    mock_security_service.create_worm_export.return_value = mock_export_obj

    with client.session_transaction() as session:
        session['username'] = 'auditor_test'

    response = client.post('/v1/compliance/worm-export', json={'export_id': 'WORM-123'})

    assert response.status_code == 201
    assert response.get_json() == mock_export_obj

    mock_audit_ledger.get_logs.assert_called_once()
    mock_security_service.create_worm_export.assert_called_once_with(
        'WORM-123', mock_logs, 'auditor_test'
    )

@patch('app.dispatch_engine')
def test_cloned_repo_unit_005_emergency_dispatch_creation(mock_dispatch_engine, client):
    """Verifies the emergency dispatch creation logic and orchestration.

    test_id: cloned_repo__unit__005
    target: create_emergency_dispatch
    requirement_id: BO-1, BO-4
    ac_ids: BO-1-AC-1, BO-4-AC-1
    """
    mock_dispatch_obj = {
        'dispatch_id': 'disp-12345',
        'status': 'INITIATED',
        'required_abo': 'O',
        'required_rh': 'NEGATIVE'
    }
    mock_dispatch_engine.create_dispatch.return_value = mock_dispatch_obj

    dispatch_data = {
        "hospital_id": "hosp-emergency",
        "severity": "LEVEL_1_CATASTROPHIC",
        "required_abo": "O",
        "required_rh": "NEGATIVE",
        "units_requested": 5
    }

    response = client.post('/v1/emergency/dispatch', json=dispatch_data)

    assert response.status_code == 201
    assert response.get_json() == mock_dispatch_obj

    # Verify the orchestration calls
    mock_dispatch_engine.create_dispatch.assert_called_once()
    mock_dispatch_engine.enqueue_sqs_message.assert_called_once()
    mock_dispatch_engine.process_sqs_worker.assert_called_once()
