"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-05-22T14:00:27.021281Z
"""

import pytest
import io
from unittest.mock import patch
from app import app

@pytest.fixture
def client():
    """A test client for the app."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client

def test_home_function_renders_template(client):
    """Verifies that the home() function redirects unauthenticated users.

    test_id: cloned_repo__unit__001
    target: home
    requirement_id: no requirement
    """
    response = client.get('/')
    assert response.status_code == 302
    assert response.location == '/login/hospital'

def test_login_hospital_function_handles_successful_authentication(client):
    """Verifies successful hospital login redirects and sets the session.

    test_id: cloned_repo__unit__002
    target: login_hospital
    requirement_id: REQ-001
    """
    with patch('app.audit_logs', []) as mock_logs:
        response = client.post('/login/hospital', data={'username': 'test_hospital', 'password': 'password'})
        assert response.status_code == 302
        assert response.location == '/hospital/dashboard'
        with client.session_transaction() as sess:
            assert sess['username'] == 'test_hospital'
            assert sess['role'] == 'hospital'
        assert len(mock_logs) == 1
        assert mock_logs[0]['action'] == 'USER LOGIN'

def test_login_admin_function_handles_successful_authentication(client):
    """Verifies successful admin login redirects and sets the session.

    test_id: cloned_repo__unit__003
    target: login_admin
    requirement_id: REQ-001
    """
    with patch('app.audit_logs', []) as mock_logs:
        response = client.post('/login/admin', data={'username': 'test_admin', 'password': 'password'})
        assert response.status_code == 302
        assert response.location == '/admin/queue'
        with client.session_transaction() as sess:
            assert sess['username'] == 'test_admin'
            assert sess['role'] == 'admin'
        assert len(mock_logs) == 1
        assert mock_logs[0]['action'] == 'ADMIN LOGIN'

def test_create_demand_function_saves_valid_data(client):
    """Verifies that create_demand saves valid data and redirects.

    test_id: cloned_repo__unit__004
    target: create_demand
    requirement_id: REQ-002, REQ-F-004, REQ-F-005
    """
    with client.session_transaction() as sess:
        sess['username'] = 'test_hospital'
        sess['role'] = 'hospital'

    mock_demands = []
    mock_logs = []
    file_data = (io.BytesIO(b"compliance doc"), "test.pdf")

    with patch('app.demands', mock_demands), patch('app.audit_logs', mock_logs):
        response = client.post(
            '/hospital/create-demand',
            data={
                'blood_type': 'A+',
                'units': '5',
                'document': file_data,
                'notes': 'Urgent'
            },
            content_type='multipart/form-data'
        )

    assert response.status_code == 302
    assert response.location == '/hospital/dashboard'
    assert len(mock_demands) == 1
    created_demand = mock_demands[0]
    assert created_demand['hospital'] == 'test_hospital'
    assert created_demand['blood_type'] == 'A+'
    assert created_demand['units'] == 5
    assert created_demand['filename'] == 'test.pdf'
    assert created_demand['status'] == 'Pending'
    assert len(mock_logs) == 1
    assert mock_logs[0]['action'] == 'BLOOD DEMAND CREATED'

def test_verify_demand_function_approves_a_request(client):
    """Verifies that an admin can approve a demand.

    test_id: cloned_repo__unit__005
    target: verify_demand
    requirement_id: REQ-003, REQ-F-006, REQ-F-017
    """
    with client.session_transaction() as sess:
        sess['username'] = 'test_admin'
        sess['role'] = 'admin'

    mock_demand = {
        "id": 99,
        "hospital": "Test Hospital",
        "blood_type": "B-",
        "units": 2,
        "filename": "doc.pdf",
        "status": "Pending"
    }
    mock_demands = [mock_demand]
    mock_alerts = []
    mock_logs = []

    with patch('app.demands', mock_demands), patch('app.alerts', mock_alerts), patch('app.audit_logs', mock_logs):
        response = client.post('/admin/verify/99', data={'action': 'approve'})

    assert response.status_code == 302
    assert response.location == '/admin/queue'
    assert mock_demand['status'] == 'Approved'
    assert len(mock_alerts) == 1
    assert mock_alerts[0]['blood_type'] == 'B-'
    assert len(mock_logs) == 1
    assert mock_logs[0]['action'] == 'EMERGENCY DEMAND APPROVED'

def test_hospital_dashboard_function_requires_authentication(client):
    """Verifies that hospital_dashboard requires authentication.

    test_id: cloned_repo__unit__006
    target: hospital_dashboard
    requirement_id: REQ-N-007
    """
    response = client.get('/hospital/dashboard')
    assert response.status_code == 302
    assert response.location == '/login/hospital'

def test_admin_audit_log_function_fetches_logs(client):
    """Verifies that admin_audit_log fetches and displays logs.

    test_id: cloned_repo__unit__007
    target: admin_audit_log
    requirement_id: REQ-003, REQ-F-006
    """
    with client.session_transaction() as sess:
        sess['username'] = 'test_admin'
        sess['role'] = 'admin'

    mock_logs = [
        {
            "action": "TEST LOG",
            "details": "This is a test log entry.",
            "user": "System",
            "timestamp": "2023-01-01 12:00:00"
        }
    ]

    with patch('app.audit_logs', mock_logs):
        response = client.get('/admin/audit-log')

    assert response.status_code == 200
    assert b"TEST LOG" in response.data
    assert b"This is a test log entry." in response.data
