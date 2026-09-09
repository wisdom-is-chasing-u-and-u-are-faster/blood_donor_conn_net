"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-25T18:14:49.006138Z
"""
import pytest
import io
from unittest.mock import patch

from app import app

@pytest.fixture
def client():
    """A test client for the app."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_verify_demand_triggers_event_on_approval(client):
    """Verify that `verify_demand` function triggers an event on approval.

    test_id: cloned_repo__unit__001
    target: verify_demand
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    initial_demands = [
        {"id": 1, "status": "Approved"},
        {"id": 2, "hospital": "General Hospital", "blood_type": "O-", "units": 4, "status": "Pending"}
    ]
    alerts_list = []
    audit_logs_list = []

    with patch('app.demands', initial_demands), \
         patch('app.alerts', alerts_list), \
         patch('app.audit_logs', audit_logs_list):
        with client.session_transaction() as sess:
            sess['role'] = 'admin'
            sess['username'] = 'test_admin'

        response = client.post('/admin/verify/2', data={'action': 'approve'})

        assert response.status_code == 302
        assert initial_demands[1]['status'] == 'Approved'
        assert len(alerts_list) == 1
        assert alerts_list[0]['status'] == 'Active'
        assert alerts_list[0]['blood_type'] == 'O-'
        assert len(audit_logs_list) == 1
        assert audit_logs_list[0]['action'] == 'EMERGENCY DEMAND APPROVED'
        assert 'Approved demand #2' in audit_logs_list[0]['details']

def test_admin_audit_log_formats_data_correctly(client):
    """Verify `admin_audit_log` function correctly formats log data.

    test_id: cloned_repo__unit__002
    target: admin_audit_log
    requirement_id: REQ-N-012, REQ-N-011
    ac_ids: REQ-N-012-AC-1, REQ-N-011-AC-1
    """
    mock_log_data = [
        {"action": "OLD_ACTION", "details": "...", "user": "System", "timestamp": "2023-01-01 10:00:00"},
        {"action": "NEW_ACTION", "details": "...", "user": "test_admin", "timestamp": "2023-01-02 12:00:00"},
        {"action": "MID_ACTION", "details": "...", "user": "System", "timestamp": "2023-01-01 15:00:00"}
    ]
    expected_sorted_data = sorted(mock_log_data, key=lambda x: x['timestamp'], reverse=True)

    with patch('app.audit_logs', mock_log_data), \
         patch('app.render_template') as mock_render_template:
        mock_render_template.return_value = "Success"
        with client.session_transaction() as sess:
            sess['role'] = 'admin'

        response = client.get('/admin/audit-log')

        assert response.status_code == 200
        mock_render_template.assert_called_once_with("audit_log.html", logs=expected_sorted_data)

def test_create_demand_persists_new_demand(client):
    """Verify `create_demand` function attempts to persist a new demand.

    test_id: cloned_repo__unit__003
    target: create_demand
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    initial_demands = []
    initial_audit_logs = []
    
    form_data = {
        'blood_type': 'AB+',
        'units': '3',
        'notes': 'Urgent case',
        'document': (io.BytesIO(b'compliance data'), 'compliance.pdf')
    }

    with patch('app.demands', initial_demands), \
         patch('app.audit_logs', initial_audit_logs):
        with client.session_transaction() as sess:
            sess['role'] = 'hospital'
            sess['username'] = 'test_hospital'

        response = client.post('/hospital/create-demand', data=form_data, content_type='multipart/form-data')

        assert response.status_code == 302
        assert len(initial_demands) == 1
        new_demand = initial_demands[0]
        assert new_demand['id'] == 1
        assert new_demand['hospital'] == 'test_hospital'
        assert new_demand['blood_type'] == 'AB+'
        assert new_demand['units'] == 3
        assert new_demand['filename'] == 'compliance.pdf'
        assert new_demand['status'] == 'Pending'
        assert len(initial_audit_logs) == 1
        new_log = initial_audit_logs[0]
        assert new_log['action'] == 'BLOOD DEMAND CREATED'
        assert 'Demand #1 (AB+, 3 units)' in new_log['details']
        assert new_log['user'] == 'test_hospital'
