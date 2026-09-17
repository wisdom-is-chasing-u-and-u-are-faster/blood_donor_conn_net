import pytest
from unittest.mock import patch, MagicMock
import io
import datetime
from app import app

"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-06-21T15:43:01.593943Z
"""

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_create_demand_processes_valid_request(client, monkeypatch):
    """Verifies create_demand processes a valid request and logs the action.

    test_id: cloned_repo__unit__001
    target: create_demand
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    monkeypatch.setattr('app.demands', [])
    monkeypatch.setattr('app.audit_logs', [])

    with client.session_transaction() as sess:
        sess['username'] = 'test_hospital'
        sess['role'] = 'hospital'

    form_data = {
        'blood_type': 'A+',
        'units': '5',
        'notes': 'Urgent request',
        'document': (io.BytesIO(b'compliance data'), 'compliance.pdf')
    }

    response = client.post('/hospital/create-demand', data=form_data, content_type='multipart/form-data')

    assert response.status_code == 302
    assert response.location == '/hospital/dashboard'
    assert len(app.demands) == 1
    assert app.demands[0]['blood_type'] == 'A+'
    assert app.demands[0]['units'] == 5
    assert app.demands[0]['hospital'] == 'test_hospital'
    assert len(app.audit_logs) == 1
    assert 'BLOOD DEMAND CREATED' in app.audit_logs[0]['action']

def test_create_demand_triggers_creation_logic(client, monkeypatch):
    """Verifies create_demand correctly adds a new demand to the system.

    test_id: cloned_repo__unit__002
    target: create_demand
    requirement_id: REQ-F-007
    ac_ids: REQ-F-007-AC-1
    """
    monkeypatch.setattr('app.demands', [])
    monkeypatch.setattr('app.audit_logs', [])

    with client.session_transaction() as sess:
        sess['username'] = 'geo_hospital'
        sess['role'] = 'hospital'

    form_data = {
        'blood_type': 'O-',
        'units': '2',
        'notes': 'Geofenced test',
        'document': (io.BytesIO(b'geo compliance'), 'geo_compliance.pdf')
    }

    response = client.post('/hospital/create-demand', data=form_data, content_type='multipart/form-data')

    assert response.status_code == 302
    assert len(app.demands) == 1
    new_demand = app.demands[0]
    assert new_demand['blood_type'] == 'O-'
    assert new_demand['hospital'] == 'geo_hospital'
    assert new_demand['status'] == 'Pending'

def test_login_admin_handles_authentication(client, monkeypatch):
    """Verifies the admin login function for both valid and invalid credentials.

    test_id: cloned_repo__unit__003
    target: login_admin
    requirement_id: CONSTRAINT-016
    ac_ids: CONSTRAINT-016-AC-2
    """
    monkeypatch.setattr('app.audit_logs', [])

    # Test valid login
    response_valid = client.post('/login/admin', data={'username': 'admin', 'password': 'password'})
    assert response_valid.status_code == 302
    assert response_valid.location == '/admin/queue'
    with client.session_transaction() as sess:
        assert sess['username'] == 'admin'
        assert sess['role'] == 'admin'
    assert len(app.audit_logs) == 1
    assert 'ADMIN LOGIN' in app.audit_logs[0]['action']

    # Test invalid login (missing password)
    response_invalid = client.post('/login/admin', data={'username': 'admin', 'password': ''})
    assert response_invalid.status_code == 200
    assert b'Invalid credentials.' in response_invalid.data
    with client.session_transaction() as sess:
        assert 'username' not in sess
        assert 'role' not in sess

def test_admin_audit_log_retrieves_logs(client, monkeypatch):
    """Verifies the admin_audit_log function correctly retrieves and displays logs.

    test_id: cloned_repo__unit__004
    target: admin_audit_log
    requirement_id: CONSTRAINT-016
    ac_ids: CONSTRAINT-016-AC-1
    """
    mock_logs = [
        {
            'action': 'TEST ACTION',
            'details': 'This is a test log entry.',
            'user': 'test_user',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    monkeypatch.setattr('app.audit_logs', mock_logs)

    with client.session_transaction() as sess:
        sess['username'] = 'audit_admin'
        sess['role'] = 'admin'

    response = client.get('/admin/audit-log')

    assert response.status_code == 200
    assert b'This is a test log entry.' in response.data
    assert b'TEST ACTION' in response.data
