"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-05-14T15:35:14.234567Z
"""
import pytest
from unittest.mock import patch, MagicMock
import io
from datetime import datetime

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_cloned_repo__unit__001(client):
    """Verify that `verify_demand` function triggers an event on approval.

    test_id: cloned_repo__unit__001
    target: verify_demand
    requirement_id: REQ-F-017,REQ-F-001
    ac_ids: REQ-F-017-AC-1,REQ-F-001-AC-1
    """
    mock_demands = [
        {
            "id": 2,
            "hospital": "General Hospital",
            "blood_type": "O-",
            "units": 4,
            "filename": "compliance_doc_B.pdf",
            "status": "Pending"
        }
    ]
    mock_alerts = []
    mock_audit_logs = []

    with patch('app.demands', mock_demands), \
         patch('app.alerts', mock_alerts), \
         patch('app.audit_logs', mock_audit_logs):
        with client.session_transaction() as sess:
            sess['role'] = 'admin'
            sess['username'] = 'test_admin'

        response = client.post('/admin/verify/2', data={'action': 'approve'})

        assert response.status_code == 302, "Redirect is expected after action"
        assert mock_demands[0]['status'] == 'Approved', "Demand status should be updated to Approved"
        assert len(mock_alerts) == 1, "An alert should be created"
        assert mock_alerts[0]['blood_type'] == 'O-'
        assert len(mock_audit_logs) == 1, "An audit log should be created"
        assert mock_audit_logs[0]['action'] == 'EMERGENCY DEMAND APPROVED'

def test_cloned_repo__unit__002(client):
    """Verify that `admin_audit_log` function fetches audit data.

    test_id: cloned_repo__unit__002
    target: admin_audit_log
    requirement_id: REQ-N-012,REQ-N-011
    ac_ids: REQ-N-012-AC-1,REQ-N-011-AC-1
    """
    mock_logs_data = [
        {
            "action": "TEST LOG",
            "details": "This is a test log entry.",
            "user": "test_user",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    with patch('app.audit_logs', mock_logs_data), \
         patch('app.render_template') as mock_render_template:
        mock_render_template.return_value = ""
        with client.session_transaction() as sess:
            sess['role'] = 'admin'

        response = client.get('/admin/audit-log')

        assert response.status_code == 200
        mock_render_template.assert_called_once()
        called_args, called_kwargs = mock_render_template.call_args
        assert called_args[0] == 'audit_log.html'
        assert 'logs' in called_kwargs
        assert called_kwargs['logs'] == sorted(mock_logs_data, key=lambda x: x["timestamp"], reverse=True)

def test_cloned_repo__unit__003(client):
    """Verify that `create_demand` function handles document processing and persistence logic.

    test_id: cloned_repo__unit__003
    target: create_demand
    requirement_id: REQ-F-015
    ac_ids: REQ-F-015-AC-1
    """
    mock_demands = []
    mock_audit_logs = []
    with patch('app.demands', mock_demands), \
         patch('app.audit_logs', mock_audit_logs):
        with client.session_transaction() as sess:
            sess['role'] = 'hospital'
            sess['username'] = 'test_hospital'

        data = {
            'blood_type': 'B+',
            'units': '3',
            'document': (io.BytesIO(b'fake-doc-content'), 'test_doc.pdf')
        }
        response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')

        assert response.status_code == 302
        assert response.location == '/hospital/dashboard'
        assert len(mock_demands) == 1
        assert mock_demands[0]['blood_type'] == 'B+'
        assert mock_demands[0]['units'] == 3
        assert mock_demands[0]['filename'] == 'test_doc.pdf'
        assert mock_demands[0]['status'] == 'Pending'
        assert len(mock_audit_logs) == 1
        assert mock_audit_logs[0]['action'] == 'BLOOD DEMAND CREATED'

def test_cloned_repo__unit__004(client):
    """Verify that `create_demand` function requires authentication.

    test_id: cloned_repo__unit__004
    target: create_demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    # Test POST without session
    response_post = client.post('/hospital/create-demand', data={})
    assert response_post.status_code == 302
    assert '/login/hospital' in response_post.location

    # Test GET without session
    response_get = client.get('/hospital/create-demand')
    assert response_get.status_code == 302
    assert '/login/hospital' in response_get.location
