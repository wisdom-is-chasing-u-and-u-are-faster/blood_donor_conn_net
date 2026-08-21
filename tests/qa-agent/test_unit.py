u"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-12T12:00:00Z
"""
import pytest
from unittest.mock import patch, MagicMock
from app import app
from datetime import datetime

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_verify_demand_triggers_event(client, monkeypatch):
    """Verifies that approving a demand triggers an event by adding to the alerts list.

    test_id: cloned_repo__unit__001
    target: verify_demand
    requirement_id: REQ-F-017,REQ-F-001
    ac_ids: REQ-F-017-AC-1,REQ-F-001-AC-1
    """
    mock_demands = [
        {
            "id": 1,
            "hospital": "Test Hospital",
            "blood_type": "A+",
            "units": 5,
            "filename": "test.pdf",
            "status": "Pending"
        }
    ]
    mock_alerts = []
    mock_audit_logs = []

    monkeypatch.setattr('app.demands', mock_demands)
    monkeypatch.setattr('app.alerts', mock_alerts)
    monkeypatch.setattr('app.audit_logs', mock_audit_logs)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.post('/admin/verify/1', data={'action': 'approve'})

    assert response.status_code == 302
    assert response.location == '/admin/queue'
    assert len(mock_alerts) == 1
    assert mock_alerts[0]['hospital'] == 'Test Hospital'
    assert mock_alerts[0]['blood_type'] == 'A+'
    assert mock_alerts[0]['status'] == 'Active'
    assert len(mock_audit_logs) == 1
    assert mock_audit_logs[0]['action'] == 'EMERGENCY DEMAND APPROVED'

def test_admin_audit_log_retrieves_data(client, monkeypatch):
    """Verifies that the admin_audit_log function correctly retrieves and passes audit log data to the template.

    test_id: cloned_repo__unit__002
    target: admin_audit_log
    requirement_id: REQ-N-012,REQ-N-011
    ac_ids: REQ-N-012-AC-1,REQ-N-011-AC-1
    """
    mock_logs = [
        {
            "action": "TEST ACTION",
            "details": "This is a test log entry.",
            "user": "test_user",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    monkeypatch.setattr('app.audit_logs', mock_logs)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'

    with patch('app.render_template') as mock_render_template:
        mock_render_template.return_value = "OK"
        response = client.get('/admin/audit-log')

        assert response.status_code == 200
        mock_render_template.assert_called_once()
        
        # Check that the 'logs' argument passed to render_template is correct
        call_args, call_kwargs = mock_render_template.call_args
        assert call_kwargs['logs'] == mock_logs
        assert call_args[0] == 'audit_log.html'

def test_create_demand_requires_authentication(client):
    """Verifies that the create_demand function redirects unauthenticated users.

    test_id: cloned_repo__unit__003
    target: create_demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    # Test GET request without session
    response_get = client.get('/hospital/create-demand')
    assert response_get.status_code == 302
    assert response_get.location == '/login/hospital'

    # Test POST request without session
    response_post = client.post('/hospital/create-demand', data={'blood_type': 'A+'})
    assert response_post.status_code == 302
    assert response_post.location == '/login/hospital'

    # Test with wrong role
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
    
    response_wrong_role = client.get('/hospital/create-demand')
    assert response_wrong_role.status_code == 302
    assert response_wrong_role.location == '/login/hospital'
