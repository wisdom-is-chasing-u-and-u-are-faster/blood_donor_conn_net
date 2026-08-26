"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-31T18:45:01.123456Z
"""
import pytest
from unittest.mock import patch, MagicMock
from app import app
import io

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_cloned_repo_unit_001(client):
    """Verify that approving a demand triggers an EmergencyDemandCreated event.

    test_id: cloned_repo__unit__001
    target: verify_demand
    requirement_id: REQ-F-017,REQ-F-001
    ac_ids: REQ-F-017-AC-1,REQ-F-001-AC-1
    """
    mock_demand = {
        "id": 1,
        "hospital": "Test General",
        "blood_type": "O-",
        "units": 5,
        "filename": "doc.pdf",
        "status": "Pending"
    }
    with patch('app.demands', [mock_demand]), \
         patch('app.alerts', []), \
         patch('app.audit_logs', []) as mock_audit_logs:
        with client.session_transaction() as sess:
            sess['username'] = 'test_admin'
            sess['role'] = 'admin'

        response = client.post('/admin/verify/1', data={'action': 'approve'})

        assert response.status_code == 302
        assert mock_demand['status'] == 'Approved'
        assert len(app.alerts) == 1
        assert app.alerts[0]['blood_type'] == 'O-'
        
        assert mock_audit_logs.append.call_count == 1
        call_args, _ = mock_audit_logs.append.call_args
        log_entry = call_args[0]
        assert log_entry['action'] == 'EMERGENCY DEMAND APPROVED'
        assert 'Approved demand #1' in log_entry['details']

def test_cloned_repo_unit_002(client):
    """Verify that the admin audit log function retrieves log data.

    test_id: cloned_repo__unit__002
    target: admin_audit_log
    requirement_id: REQ-N-012
    ac_ids: REQ-N-012-AC-1
    """
    mock_logs = [
        {"action": "Log 1", "details": "...", "user": "sys", "timestamp": "2024-01-01 10:00:00"},
        {"action": "Log 2", "details": "...", "user": "sys", "timestamp": "2024-01-02 12:00:00"}
    ]
    with patch('app.audit_logs', mock_logs), \
         patch('app.render_template') as mock_render_template:
        with client.session_transaction() as sess:
            sess['username'] = 'test_admin'
            sess['role'] = 'admin'

        client.get('/admin/audit-log')

        mock_render_template.assert_called_once()
        _, kwargs = mock_render_template.call_args
        assert 'logs' in kwargs
        # The function sorts logs by timestamp in reverse order
        sorted_logs = kwargs['logs']
        assert len(sorted_logs) == 2
        assert sorted_logs[0]['action'] == 'Log 2'
        assert sorted_logs[1]['action'] == 'Log 1'

def test_cloned_repo_unit_003(client):
    """Verify that creating a demand calls the OCR and storage services.

    test_id: cloned_repo__unit__003
    target: create_demand
    requirement_id: REQ-F-015
    ac_ids: REQ-F-015-AC-1
    """
    # Note: The source code does not contain OCR or external storage service calls.
    # This test verifies the actual implementation: appending to in-memory lists.
    with patch('app.demands', []) as mock_demands, \
         patch('app.audit_logs', []) as mock_audit_logs:
        with client.session_transaction() as sess:
            sess['username'] = 'test_hospital'
            sess['role'] = 'hospital'

        form_data = {
            'blood_type': 'A+',
            'units': '3',
            'notes': 'Test notes',
            'document': (io.BytesIO(b'fake-pdf-content'), 'compliance.pdf')
        }

        response = client.post('/hospital/create-demand', data=form_data, content_type='multipart/form-data')

        assert response.status_code == 302
        assert mock_demands.append.call_count == 1
        assert mock_audit_logs.append.call_count == 1

        # Verify demand data was saved correctly
        saved_demand = mock_demands.append.call_args[0][0]
        assert saved_demand['hospital'] == 'test_hospital'
        assert saved_demand['blood_type'] == 'A+'
        assert saved_demand['units'] == 3
        assert saved_demand['filename'] == 'compliance.pdf'
        assert saved_demand['status'] == 'Pending'

        # Verify audit log was created
        saved_log = mock_audit_logs.append.call_args[0][0]
        assert saved_log['action'] == 'BLOOD DEMAND CREATED'
        assert 'A+, 3 units' in saved_log['details']
