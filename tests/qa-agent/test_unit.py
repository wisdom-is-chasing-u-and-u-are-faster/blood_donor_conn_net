import pytest
from app import app
from unittest.mock import patch
import datetime

"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-18T13:01:23.905204Z
"""

@pytest.fixture
def client():
    """A test client for the app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_cloned_repo_unit_001(client, monkeypatch):
    """Verify that verify_demand function logic correctly processes a demand.

    test_id: cloned_repo__unit__001
    target: verify_demand
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    mock_demands = [
        {"id": 1, "status": "Approved", "hospital": "General", "blood_type": "A+"},
        {"id": 2, "status": "Pending", "hospital": "City", "blood_type": "O-"}
    ]
    mock_alerts = []
    mock_audit_logs = []

    monkeypatch.setattr('app.demands', mock_demands)
    monkeypatch.setattr('app.alerts', mock_alerts)
    monkeypatch.setattr('app.audit_logs', mock_audit_logs)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.post('/admin/verify/2', data={'action': 'approve'})

    assert response.status_code == 302
    assert response.location == '/admin/queue'

    verified_demand = next((d for d in mock_demands if d['id'] == 2), None)
    assert verified_demand is not None
    assert verified_demand['status'] == 'Approved'

    assert len(mock_alerts) == 1
    assert mock_alerts[0]['hospital'] == 'City'
    assert mock_alerts[0]['blood_type'] == 'O-'

    assert len(mock_audit_logs) == 1
    assert "Approved demand #2" in mock_audit_logs[0]['details']

def test_cloned_repo_unit_002(client, monkeypatch):
    """Verify that admin_audit_log function retrieves log data.

    test_id: cloned_repo__unit__002
    target: admin_audit_log
    requirement_id: REQ-N-012,REQ-N-011
    ac_ids: REQ-N-012-AC-1,REQ-N-011-AC-1
    """
    mock_logs = [
        {"timestamp": "2023-01-01 10:00:00", "action": "LOGIN", "details": "User logged in", "user": "testuser"},
        {"timestamp": "2023-01-01 11:00:00", "action": "ACTION", "details": "User did something", "user": "testuser"}
    ]
    monkeypatch.setattr('app.audit_logs', mock_logs)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'

    response = client.get('/admin/audit-log')

    assert response.status_code == 200
    assert b"User logged in" in response.data
    assert b"User did something" in response.data
    assert response.data.find(b"User did something") < response.data.find(b"User logged in")

def test_cloned_repo_unit_003(client):
    """Verify that create_demand function checks for authentication.

    test_id: cloned_repo__unit__003
    target: create_demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    response_unauth = client.get('/hospital/create-demand')
    
    assert response_unauth.status_code == 302
    assert response_unauth.location == '/login/hospital'

    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'

    response_auth = client.get('/hospital/create-demand')

    assert response_auth.status_code == 200
