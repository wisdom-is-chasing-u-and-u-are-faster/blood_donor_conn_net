import pytest
from unittest.mock import patch
from datetime import datetime

from app import app


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


def test_verify_demand_triggers_event(client, monkeypatch):
    """Verifies that approving a demand updates its status and logs an event.

    test_id: cloned_repo__unit__001
    target: verify_demand
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    mock_demands = [
        {
            "id": 1,
            "hospital": "Test Hospital",
            "blood_type": "A+",
            "units": 5,
            "status": "Pending"
        }
    ]
    mock_alerts = []
    mock_audit_logs = []

    monkeypatch.setattr('app.demands', mock_demands)
    monkeypatch.setattr('app.alerts', mock_alerts)
    monkeypatch.setattr('app.audit_logs', mock_audit_logs)

    with client.session_transaction() as sess:
        sess['username'] = 'test_admin'
        sess['role'] = 'admin'

    response = client.post('/admin/verify/1', data={'action': 'approve'})

    assert response.status_code == 302
    assert mock_demands[0]['status'] == 'Approved'
    assert len(mock_alerts) == 1
    assert mock_alerts[0]['blood_type'] == 'A+'
    assert len(mock_audit_logs) == 1
    assert 'EMERGENCY DEMAND APPROVED' in mock_audit_logs[0]['action']
    assert 'Emitted event' in mock_audit_logs[0]['details']


def test_admin_audit_log_retrieves_data(client, monkeypatch):
    """Verifies that the admin audit log page displays log data.

    test_id: cloned_repo__unit__002
    target: admin_audit_log
    requirement_id: REQ-N-012,REQ-N-011
    ac_ids: REQ-N-012-AC-1,REQ-N-011-AC-1
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mock_logs = [
        {
            "action": "TEST ACTION",
            "details": "This is a unique test log entry.",
            "user": "TestUser",
            "timestamp": timestamp
        }
    ]
    monkeypatch.setattr('app.audit_logs', mock_logs)

    with client.session_transaction() as sess:
        sess['username'] = 'test_admin'
        sess['role'] = 'admin'

    response = client.get('/admin/audit-log')

    assert response.status_code == 200
    assert b'This is a unique test log entry.' in response.data
    assert b'TEST ACTION' in response.data
    assert b'TestUser' in response.data


def test_create_demand_requires_authentication(client):
    """Verifies that creating a demand requires a hospital session.

    test_id: cloned_repo__unit__003
    target: create_demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    # Test GET request without authentication
    response_get = client.get('/hospital/create-demand')
    assert response_get.status_code == 302
    assert '/login/hospital' in response_get.location

    # Test POST request without authentication
    response_post = client.post('/hospital/create-demand', data={
        'blood_type': 'A+',
        'units': '5'
    })
    assert response_post.status_code == 302
    assert '/login/hospital' in response_post.location
