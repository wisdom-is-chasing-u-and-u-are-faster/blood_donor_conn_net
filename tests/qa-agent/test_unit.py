import pytest
from unittest.mock import patch, MagicMock
import io
from datetime import datetime

"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-05-24T13:01:01.844356Z
"""

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_verify_demand_triggers_event(client, monkeypatch):
    """Verify that verify_demand function triggers an event.

    test_id: cloned_repo__unit__001
    target: verify_demand
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    mock_demands = [
        {
            "id": 99,
            "hospital": "Test Hospital",
            "blood_type": "B+",
            "units": 5,
            "filename": "test_doc.pdf",
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

    client.post('/admin/verify/99', data={'action': 'approve'})

    assert len(mock_audit_logs) > 0
    approval_log = next((log for log in mock_audit_logs if log['action'] == 'EMERGENCY DEMAND APPROVED'), None)
    assert approval_log is not None
    assert 'Approved demand #99' in approval_log['details']
    assert 'Emitted event' in approval_log['details']
    assert mock_demands[0]['status'] == 'Approved'
    assert len(mock_alerts) == 1
    assert mock_alerts[0]['blood_type'] == 'B+'

def test_admin_audit_log_formats_data(client, monkeypatch):
    """Verify admin_audit_log function correctly formats log data.

    test_id: cloned_repo__unit__002
    target: admin_audit_log
    requirement_id: REQ-N-012
    ac_ids: REQ-N-012-AC-1
    """
    sample_logs = [
        {
            "action": "TEST ACTION",
            "details": "This is a test log.",
            "user": "test_user",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    monkeypatch.setattr('app.audit_logs', sample_logs)

    with patch('app.render_template') as mock_render_template:
        mock_render_template.return_value = "ok"
        with client.session_transaction() as sess:
            sess['username'] = 'test_admin'
            sess['role'] = 'admin'

        client.get('/admin/audit-log')

        mock_render_template.assert_called_once()
        args, kwargs = mock_render_template.call_args
        assert args[0] == 'audit_log.html'
        assert 'logs' in kwargs
        assert len(kwargs['logs']) == 1
        assert kwargs['logs'][0]['action'] == 'TEST ACTION'

def test_create_demand_attempts_to_save_data(client, monkeypatch):
    """Verify create_demand function attempts to save data.

    test_id: cloned_repo__unit__003
    target: create_demand
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    mock_demands = []
    mock_audit_logs = []
    monkeypatch.setattr('app.demands', mock_demands)
    monkeypatch.setattr('app.audit_logs', mock_audit_logs)

    with client.session_transaction() as sess:
        sess['username'] = 'test_hospital'
        sess['role'] = 'hospital'

    form_data = {
        'blood_type': 'A-',
        'units': '3',
        'notes': 'Urgent need',
        'document': (io.BytesIO(b'fake-pdf-content'), 'compliance.pdf')
    }

    response = client.post('/hospital/create-demand', data=form_data, content_type='multipart/form-data')

    assert response.status_code == 302
    assert len(mock_demands) == 1
    saved_demand = mock_demands[0]
    assert saved_demand['blood_type'] == 'A-'
    assert saved_demand['units'] == 3
    assert saved_demand['hospital'] == 'test_hospital'
    assert saved_demand['status'] == 'Pending'
    assert saved_demand['filename'] == 'compliance.pdf'

    assert len(mock_audit_logs) == 1
    assert 'BLOOD DEMAND CREATED' in mock_audit_logs[0]['action']

def test_create_demand_requires_authentication(client, monkeypatch):
    """Verify create_demand function requires authentication.

    test_id: cloned_repo__unit__004
    target: create_demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    initial_demands_count = len(app.demands)

    # Ensure session is empty
    with client.session_transaction() as sess:
        sess.clear()

    form_data = {
        'blood_type': 'B+',
        'units': '2',
        'document': (io.BytesIO(b'content'), 'test.pdf')
    }
    response = client.post('/hospital/create-demand', data=form_data, content_type='multipart/form-data')

    # Should redirect to login page
    assert response.status_code == 302
    assert 'login/hospital' in response.location

    # Core logic should not have been executed
    assert len(app.demands) == initial_demands_count
