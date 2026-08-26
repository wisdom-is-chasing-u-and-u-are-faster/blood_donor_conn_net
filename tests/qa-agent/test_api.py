import pytest
from app import app
import datetime
from unittest.mock import patch
from io import BytesIO

"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2024-07-24T18:08:24.238911Z
"""

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_cloned_repo_api_001(client, monkeypatch):
    """Verifies an admin can retrieve the audit log.

    test_id: cloned_repo__api__001
    target: GET /admin/audit-log
    requirement_id: REQ-N-012,REQ-N-011
    ac_ids: REQ-N-012-AC-1,REQ-N-011-AC-1
    """
    mock_logs = [
        {
            'action': 'TEST_ACTION',
            'details': 'This is a test log entry.',
            'user': 'test_admin',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    monkeypatch.setattr('app.audit_logs', mock_logs)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.get('/admin/audit-log')

    assert response.status_code == 200
    assert b'TEST_ACTION' in response.data
    assert b'This is a test log entry.' in response.data

def test_cloned_repo_api_001_negative_unauthorized(client):
    """Verifies unauthenticated users are redirected from the audit log page.

    test_id: cloned_repo__api__001_negative_unauthorized
    target: GET /admin/audit-log
    requirement_id: REQ-N-012,REQ-N-011
    ac_ids: REQ-N-012-AC-1,REQ-N-011-AC-1
    """
    response = client.get('/admin/audit-log')
    assert response.status_code == 302
    assert 'login/admin' in response.location

def test_cloned_repo_api_002(client, monkeypatch):
    """Verifies an admin can approve a blood demand.

    test_id: cloned_repo__api__002
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    mock_demands = [
        {'id': 123, 'status': 'Pending', 'hospital': 'Test Hospital', 'blood_type': 'A+'}
    ]
    monkeypatch.setattr('app.demands', mock_demands)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.post('/admin/verify/123', data={'action': 'approve'})

    assert response.status_code == 302
    assert 'admin/queue' in response.location
    assert mock_demands[0]['status'] == 'Approved'

def test_cloned_repo_api_002_negative_not_found(client):
    """Verifies a 302 redirect is returned for a non-existent demand ID.

    test_id: cloned_repo__api__002_negative_not_found
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.post('/admin/verify/999', data={'action': 'approve'})

    # The app flashes a message and redirects, it does not 404.
    assert response.status_code == 302
    assert 'admin/queue' in response.location

def test_cloned_repo_api_003(client, monkeypatch):
    """Verifies a hospital user can create a new blood demand.

    test_id: cloned_repo__api__003
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    mock_demands = []
    monkeypatch.setattr('app.demands', mock_demands)

    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'

    data = {
        'blood_type': 'O-',
        'units': '3',
        'notes': 'Urgent request',
        'document': (BytesIO(b'fake compliance doc'), 'compliance.pdf')
    }
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')

    assert response.status_code == 302
    assert 'hospital/dashboard' in response.location
    assert len(mock_demands) == 1
    assert mock_demands[0]['blood_type'] == 'O-'
    assert mock_demands[0]['status'] == 'Pending'

def test_cloned_repo_api_003_negative_unauthenticated(client):
    """Verifies an unauthenticated user is redirected from create demand page.

    test_id: cloned_repo__api__003_negative_unauthenticated
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    data = {'blood_type': 'A+', 'units': '2'}
    response = client.post('/hospital/create-demand', data=data)

    assert response.status_code == 302
    assert 'login/hospital' in response.location

def test_cloned_repo_api_004_orphan(client):
    """Verifies the home page redirects to the login page.

    test_id: cloned_repo__api__004_orphan
    target: GET /
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/')
    assert response.status_code == 302
    assert 'login/hospital' in response.location

def test_cloned_repo_api_005_orphan(client):
    """Verifies the hospital login page is accessible.

    test_id: cloned_repo__api__005_orphan
    target: GET /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/login/hospital')
    assert response.status_code == 200
    assert b'Hospital Login' in response.data

def test_cloned_repo_api_006_orphan(client):
    """Verifies the hospital dashboard requires authentication and redirects.

    test_id: cloned_repo__api__006_orphan
    target: GET /hospital/dashboard
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/hospital/dashboard')
    assert response.status_code == 302
    assert 'login/hospital' in response.location

def test_cloned_repo_api_007_orphan(client):
    """Verifies the admin queue page is accessible to an admin.

    test_id: cloned_repo__api__007_orphan
    target: GET /admin/queue
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'

    response = client.get('/admin/queue')
    assert response.status_code == 200
    assert b'Verification Queue' in response.data

def test_cloned_repo_api_008_orphan(client):
    """Verifies that logging out redirects the user.

    test_id: cloned_repo__api__008_orphan
    target: GET /logout
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
        sess['role'] = 'hospital'

    response = client.get('/logout')
    assert response.status_code == 302
    assert 'login/hospital' in response.location

    # Verify session is cleared
    with client.session_transaction() as sess:
        assert 'username' not in sess
        assert 'role' not in sess
