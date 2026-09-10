"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-25T13:16:35.328903Z
"""
import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from app import app
from services.eligibility_service import fn_validate_donor_eligibility
from services.spatial_service import RedisGeospatialCache

@pytest.fixture
def client():
    """Create a Flask test client for the app."""
    app.config['TESTING'] = True
    with app.test_request_context():
        with app.test_client() as c:
            yield c

def test_cloned_repo_unit_001():
    """Verifies get_donor_eligibility function enforces 56-day whole blood donation interval.

    test_id: cloned_repo__unit__001
    target: get_donor_eligibility
    requirement_id: REQ-005
    ac_ids: REQ-005-AC-1
    """
    donor = {"username": "testdonor", "is_deferred": False}
    today = datetime.utcnow()

    # Case 1: Ineligible donor (donated 40 days ago)
    last_donation_ineligible = today - timedelta(days=40)
    history_ineligible = [{
        "donation_type": "WHOLE_BLOOD",
        "collected_at": last_donation_ineligible.isoformat() + "Z"
    }]
    result_ineligible = fn_validate_donor_eligibility(
        donor, history_ineligible, "WHOLE_BLOOD", today
    )

    assert not result_ineligible["isEligible"]
    assert result_ineligible["daysRemaining"] == 56 - 40
    assert result_ineligible["blockReason"] == "MINIMUM_DONATION_INTERVAL_NOT_MET"

    # Case 2: Eligible donor (donated 60 days ago)
    last_donation_eligible = today - timedelta(days=60)
    history_eligible = [{
        "donation_type": "WHOLE_BLOOD",
        "collected_at": last_donation_eligible.isoformat() + "Z"
    }]
    result_eligible = fn_validate_donor_eligibility(
        donor, history_eligible, "WHOLE_BLOOD", today
    )

    assert result_eligible["isEligible"]
    assert result_eligible["daysRemaining"] == 0

def test_cloned_repo_unit_002(client):
    """Verifies create_emergency_dispatch function initiates dispatch process.

    test_id: cloned_repo__unit__002
    target: create_emergency_dispatch
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-1
    """
    mock_dispatch_record = {"dispatch_id": "disp-1234", "status": "INITIATED"}
    dispatch_data = {
        "hospital_id": "hosp-test",
        "severity": "LEVEL_1_CATASTROPHIC",
        "required_abo": "O",
        "required_rh": "NEGATIVE",
        "units_requested": 2
    }

    with patch('app.dispatch_engine') as mock_engine:
        mock_engine.create_dispatch.return_value = mock_dispatch_record

        response = client.post('/v1/emergency/dispatch', json=dispatch_data)

        assert response.status_code == 201
        assert response.get_json() == mock_dispatch_record

        mock_engine.create_dispatch.assert_called_once_with(
            hospital_id=dispatch_data['hospital_id'],
            severity=dispatch_data['severity'],
            required_abo=dispatch_data['required_abo'],
            required_rh=dispatch_data['required_rh'],
            units_requested=dispatch_data['units_requested'],
            initiated_by='ER Clinician'  # Default from session
        )
        mock_engine.enqueue_sqs_message.assert_called_once()
        mock_engine.process_sqs_worker.assert_called_once()

def test_cloned_repo_unit_003():
    """Verifies find_spatial_candidates function filters candidates by distance.

    test_id: cloned_repo__unit__003
    target: find_spatial_candidates
    requirement_id: REQ-001
    ac_ids: REQ-001-AC-2
    """
    cache = RedisGeospatialCache()
    center_lat, center_lon = 37.7749, -122.4194

    # Add a candidate inside the 15km radius
    cache.geoadd("donor_inside", 37.78, -122.41, {"name": "Donor Inside"})

    # Add a candidate far outside the 15km radius
    cache.geoadd("donor_outside", 34.0522, -118.2437, {"name": "Donor Outside"})

    candidates = cache.geosearch(center_lat=center_lat, center_lon=center_lon, radius_km=15.0)

    assert len(candidates) == 1
    assert candidates[0]['member_id'] == 'donor_inside'

def test_cloned_repo_unit_004(client):
    """Verifies export_worm function calls the WORM storage writer.

    test_id: cloned_repo__unit__004
    target: export_worm
    requirement_id: REQ-003
    ac_ids: REQ-003-AC-5
    """
    mock_logs = [{"log_id": 1, "details": "some audit data"}]
    mock_export_record = {"export_id": "WORM-XYZ", "record_count": 1}

    with patch('app.audit_ledger') as mock_audit, \
         patch('app.security_service') as mock_security:
        
        mock_audit.get_logs.return_value = mock_logs
        mock_security.create_worm_export.return_value = mock_export_record

        response = client.post('/v1/compliance/worm-export', json={"export_id": "WORM-XYZ"})

        assert response.status_code == 201
        assert response.get_json() == mock_export_record

        mock_audit.get_logs.assert_called_once_with()
        mock_security.create_worm_export.assert_called_once()
        
        # Verify the correct data was passed to the WORM writer
        _, kwargs = mock_security.create_worm_export.call_args
        assert kwargs['export_id'] == 'WORM-XYZ'
        assert kwargs['records'] == mock_logs
        assert kwargs['created_by'] == 'auditor' # Default from session
