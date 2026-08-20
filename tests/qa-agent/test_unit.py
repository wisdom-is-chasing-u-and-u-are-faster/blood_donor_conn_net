"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-05-21T17:15:27.485294Z
"""
import pytest
from unittest.mock import patch, MagicMock
from app import app
from datetime import datetime
from io import BytesIO

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_verify_demand_triggers_event_on_approval(client, monkeypatch):
    """Verify `verify_demand` function triggers event on approval.

    test_id: cloned_repo__unit__001
    target: verify_demand
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    mock_demands = [
        {
            "id": 1,
            "hospital": "General Hospital",
            "blood_type": "A+",
            "units": 10,
            "filename": "compliance_doc_A.pdf",
            "status": "Approved"
        },
        {
            "id": 2,
            "hospital": "City Hospital",
            "blood_type": "O-",
            "units": 4,
            "filename": "compliance_doc_B.pdf",
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

    response = client.post('/admin/verify/2', data={'action': 'approve'})

    assert response.status_code == 302
    assert response.location == '/admin/queue'

    # Assert demand status is updated
    updated_demand = next((d for d in mock_demands if d['id'] == 2), None)
    assert updated_demand is not None
    assert updated_demand['status'] == 'Approved'

    # Assert event was published (alert was created)
    assert len(mock_alerts) == 1
    new_alert = mock_alerts[0]
    assert new_alert['hospital'] == 'City Hospital'
    assert new_alert['blood_type'] == 'O-'
    assert new_alert['status'] == 'Active'

    # Assert audit log was written
    assert len(mock_audit_logs) == 1
    assert mock_audit_logs[0]['action'] == 'EMERGENCY DEMAND APPROVED'

def test_admin_audit_log_retrieves_and_formats_data(client, monkeypatch):
    """Verify `admin_audit_log` function retrieves and formats log data.

    test_id: cloned_repo__unit__002
    target: admin_audit_log
    requirement_id: REQ-N-011,REQ-N-012
    ac_ids: REQ-N-011-AC-1,REQ-N-012-AC-1
    """
    mock_logs = [
        {
            "action": "USER LOGIN",
            "details": "User logged in",
            "user": "test_user",
            "timestamp": "2023-01-01 10:00:00"
        },
        {
            "action": "SYSTEM STARTUP",
            "details": "Service started",
            "user": "System",
            "timestamp": "2023-01-01 12:00:00"
        }
    ]
    monkeypatch.setattr('app.audit_logs', mock_logs)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'

    with patch('app.render_template') as mock_render:
        mock_render.return_value = "OK"
        response = client.get('/admin/audit-log')

    assert response.status_code == 200
    mock_render.assert_called_once()
    
    # Check that the logs passed to the template are sorted by timestamp descending
    call_args, call_kwargs = mock_render.call_args
    assert 'logs' in call_kwargs
    rendered_logs = call_kwargs['logs']
    assert len(rendered_logs) == 2
    assert rendered_logs[0]['action'] == 'SYSTEM STARTUP' # The later one
    assert rendered_logs[1]['action'] == 'USER LOGIN' # The earlier one

def test_create_demand_saves_new_demand(client, monkeypatch):
    """Verify `create_demand` function saves new demand to database.

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
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'

    form_data = {
        'blood_type': 'B+',
        'units': '5',
        'notes': 'Urgent case',
        'document': (BytesIO(b'my file contents'), 'test_doc.pdf')
    }

    response = client.post('/hospital/create-demand', data=form_data, content_type='multipart/form-data')

    assert response.status_code == 302
    assert response.location == '/hospital/dashboard'

    # Assert a new demand was created in the mocked list
    assert len(mock_demands) == 1
    new_demand = mock_demands[0]
    assert new_demand['hospital'] == 'test_hospital'
    assert new_demand['blood_type'] == 'B+'
    assert new_demand['units'] == 5
    assert new_demand['filename'] == 'test_doc.pdf'
    assert new_demand['status'] == 'Pending'

    # Assert an audit log was created
    assert len(mock_audit_logs) == 1
    assert mock_audit_logs[0]['action'] == 'BLOOD DEMAND CREATED'
    assert mock_audit_logs[0]['user'] == 'test_hospital'
