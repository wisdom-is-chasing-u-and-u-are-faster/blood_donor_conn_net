import pytest
from unittest.mock import patch, MagicMock
from app import app
import datetime

"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-18T10:09:01.996323Z
"""

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for simpler testing
    with app.test_client() as client:
        yield client

def test_cloned_repo_unit_001_verify_demand_emits_event(client):
    """Verify `verify_demand` function emits `EmergencyDemandCreated` event.

    test_id: cloned_repo__unit__001
    target: verify_demand
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    mock_demand = {
        "id": 1,
        "hospital": "Test Hospital",
        "blood_type": "A+",
        "units": 5,
        "status": "Pending"
    }
    
    with patch('app.demands', [mock_demand]), \
         patch('app.alerts', []), \
         patch('app.audit_logs', []) as mock_audit_logs:
        
        with client.session_transaction() as sess:
            sess['username'] = 'test_admin'
            sess['role'] = 'admin'

        response = client.post('/admin/verify/1', data={'action': 'approve'})

        assert response.status_code == 302 # Should redirect after action
        assert len(mock_audit_logs) == 1
        
        emitted_event = mock_audit_logs[0]
        assert emitted_event['action'] == 'EMERGENCY DEMAND APPROVED'
        assert 'Approved demand #1 (A+)' in emitted_event['details']
        assert emitted_event['user'] == 'test_admin'

def test_cloned_repo_unit_002_admin_audit_log_retrieves_data(client):
    """Verify `admin_audit_log` function retrieves data from the logging service.

    test_id: cloned_repo__unit__002
    target: admin_audit_log
    requirement_id: REQ-N-012,REQ-N-011
    ac_ids: REQ-N-012-AC-1,REQ-N-011-AC-1
    """
    mock_logs = [
        {
            "action": "TEST ACTION",
            "details": "This is a unique test log entry.",
            "user": "test_user",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    with patch('app.audit_logs', mock_logs):
        with client.session_transaction() as sess:
            sess['username'] = 'test_admin'
            sess['role'] = 'admin'

        response = client.get('/admin/audit-log')

        assert response.status_code == 200
        assert b'This is a unique test log entry.' in response.data
        assert b'TEST ACTION' in response.data

def test_cloned_repo_unit_003_create_demand_protected_by_auth(client):
    """Verify `create_demand` function logic is protected by authentication.

    test_id: cloned_repo__unit__003
    target: create_demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    # Test GET request without session
    get_response = client.get('/hospital/create-demand')
    assert get_response.status_code == 302
    assert '/login/hospital' in get_response.location

    # Test POST request without session
    post_response = client.post('/hospital/create-demand', data={
        'blood_type': 'A+',
        'units': '2',
    })
    assert post_response.status_code == 302
    assert '/login/hospital' in post_response.location

    # Test with wrong role
    with client.session_transaction() as sess:
        sess['username'] = 'test_admin'
        sess['role'] = 'admin' # Not 'hospital'
    
    wrong_role_response = client.get('/hospital/create-demand')
    assert wrong_role_response.status_code == 302
    assert '/login/hospital' in wrong_role_response.location
