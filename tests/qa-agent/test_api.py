"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2024-05-20T13:01:27.553952Z
"""
import pytest
from app import app
from unittest.mock import patch
import io

@pytest.fixture
def client():
    """A test client for the app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_cloned_repo_api_001(client, monkeypatch):
    """Admin can verify a hospital demand via API.

    test_id: cloned_repo__api__001
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    mock_demands = [{'id': 99, 'status': 'Pending', 'hospital': 'Test Hospital', 'blood_type': 'O+'}]
    monkeypatch.setattr('app.demands', mock_demands)
    monkeypatch.setattr('app.audit_logs', [])

    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.post('/admin/verify/99', data={'action': 'approve'})

    assert response.status_code == 302
    assert 'admin/queue' in response.location
    assert mock_demands[0]['status'] == 'Approved'

def test_cloned_repo_api_002(client, monkeypatch):
    """Admin can access the audit log.

    test_id: cloned_repo__api__002
    target: GET /admin/audit-log
    requirement_id: REQ-N-011,REQ-N-012
    ac_ids: REQ-N-011-AC-1,REQ-N-012-AC-1
    """
    mock_logs = [{'timestamp': '2023-01-01 12:00:00', 'action': 'TEST_ACTION', 'details': 'Details', 'user': 'User'}]
    monkeypatch.setattr('app.audit_logs', mock_logs)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'

    response = client.get('/admin/audit-log')

    assert response.status_code == 200
    assert b'TEST_ACTION' in response.data

def test_cloned_repo_api_002_negative_unauthorized(client):
    """Non-admin user cannot access the audit log.

    test_id: cloned_repo__api__002_negative_unauthorized
    target: GET /admin/audit-log
    requirement_id: REQ-N-012
    ac_ids: REQ-N-012-AC-1
    """
    response_unauth = client.get('/admin/audit-log')
    assert response_unauth.status_code == 302
    assert 'login/admin' in response_unauth.location

    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
    response_hospital = client.get('/admin/audit-log')
    assert response_hospital.status_code == 302
    assert 'login/admin' in response_hospital.location

def test_cloned_repo_api_003(client, monkeypatch):
    """Hospital can create a new blood demand.

    test_id: cloned_repo__api__003
    target: POST /hospital/create-demand
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    mock_demands = []
    monkeypatch.setattr('app.demands', mock_demands)
    monkeypatch.setattr('app.audit_logs', [])

    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'

    data = {
        'blood_type': 'B-',
        'units': '3',
        'notes': 'Urgent need',
        'document': (io.BytesIO(b'mock file content'), 'test_doc.pdf')
    }
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')

    assert response.status_code == 302
    assert 'hospital/dashboard' in response.location
    assert len(mock_demands) == 1
    assert mock_demands[0]['blood_type'] == 'B-'
    assert mock_demands[0]['units'] == 3
    assert mock_demands[0]['status'] == 'Pending'

def test_cloned_repo_api_003_negative_unauthenticated(client):
    """Unauthenticated user cannot create a blood demand.

    test_id: cloned_repo__api__003_negative_unauthenticated
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    data = {
        'blood_type': 'A+',
        'units': '2',
        'document': (io.BytesIO(b'mock file content'), 'test.pdf')
    }
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')

    assert response.status_code == 302
    assert 'login/hospital' in response.location

def test_cloned_repo_api_004(client):
    """Hospital user can log in successfully.

    test_id: cloned_repo__api__004
    target: POST /login/hospital
    requirement_id: REQ-N-004
    ac_ids: REQ-N-004-AC-1
    """
    response = client.post('/login/hospital', data={'username': 'testhospital', 'password': 'password'})
    assert response.status_code == 302
    assert 'hospital/dashboard' in response.location
    with client.session_transaction() as sess:
        assert sess.get('role') == 'hospital'
        assert sess.get('username') == 'testhospital'

def test_cloned_repo_api_005(client):
    """Admin user can log in successfully.

    test_id: cloned_repo__api__005
    target: POST /login/admin
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/admin', data={'username': 'testadmin', 'password': 'password'})
    assert response.status_code == 302
    assert 'admin/queue' in response.location
    with client.session_transaction() as sess:
        assert sess.get('role') == 'admin'
        assert sess.get('username') == 'testadmin'

def test_cloned_repo_api_006(client):
    """User can log out.

    test_id: cloned_repo__api__006
    target: GET /logout
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'testuser'

    response = client.get('/logout')
    assert response.status_code == 302
    assert 'login/hospital' in response.location
    with client.session_transaction() as sess:
        assert 'role' not in sess
        assert 'username' not in sess

def test_cloned_repo_api_007(client):
    """Authenticated hospital user can view their dashboard.

    test_id: cloned_repo__api__007
    target: GET /hospital/dashboard
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'testuser'

    response = client.get('/hospital/dashboard')
    assert response.status_code == 200

def test_cloned_repo_api_008(client):
    """Authenticated admin can view the demand queue.

    test_id: cloned_repo__api__008
    target: GET /admin/queue
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'testadmin'

    response = client.get('/admin/queue')
    assert response.status_code == 200

def test_cloned_repo_api_009(client):
    """Home page is accessible.

    test_id: cloned_repo__api__009
    target: GET /
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/')
    assert response.status_code == 302
    assert 'login/hospital' in response.location
