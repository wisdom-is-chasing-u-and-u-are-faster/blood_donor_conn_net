"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2024-07-18T15:03:46.543210Z
"""
import pytest
import io
from unittest.mock import patch
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_cloned_repo__api__001(client, monkeypatch):
    """Admin can verify a pending demand via API.

    test_id: cloned_repo__api__001
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    mock_demands = [
        {"id": 123, "hospital": "Test Hospital", "blood_type": "A+", "units": 5, "status": "Pending"}
    ]
    monkeypatch.setattr('app.demands', mock_demands)
    
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.post('/admin/verify/123', data={'action': 'approve'})

    assert response.status_code == 302 # Redirects on success
    assert mock_demands[0]['status'] == 'Approved'

def test_cloned_repo__api__001_negative_not_found(client):
    """Admin cannot verify a non-existent demand.

    test_id: cloned_repo__api__001_negative_not_found
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.post('/admin/verify/99999', data={'action': 'approve'})

    # The app flashes a message and redirects, it does not return a 404.
    assert response.status_code == 302
    with client.session_transaction() as sess:
        flashes = sess.get('_flashes', [])
        assert any('Demand request not found.' in msg[1] for msg in flashes)

def test_cloned_repo__api__001_negative_unauthorized(client):
    """Non-admin user cannot verify a demand.

    test_id: cloned_repo__api__001_negative_unauthorized
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    # Test with no authentication
    response_unauthenticated = client.post('/admin/verify/123', data={'action': 'approve'})
    assert response_unauthenticated.status_code == 302
    assert '/login/admin' in response_unauthenticated.location

    # Test with non-admin role
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'
    
    response_non_admin = client.post('/admin/verify/123', data={'action': 'approve'})
    assert response_non_admin.status_code == 302
    assert '/login/admin' in response_non_admin.location

def test_cloned_repo__api__002(client):
    """Admin can view the audit log via API.

    test_id: cloned_repo__api__002
    target: GET /admin/audit-log
    requirement_id: REQ-N-011, REQ-N-012
    ac_ids: REQ-N-011-AC-1, REQ-N-012-AC-1
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.get('/admin/audit-log')

    assert response.status_code == 200
    assert b'Audit Log' in response.data
    assert b'SYSTEM STARTUP' in response.data

def test_cloned_repo__api__003(client, monkeypatch):
    """Authenticated hospital can create a blood demand via API.

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
        'blood_type': 'O+',
        'units': '5',
        'document': (io.BytesIO(b'fake file content'), 'test.pdf'),
        'notes': 'Urgent need'
    }
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')

    assert response.status_code == 302 # Redirects to dashboard
    assert len(mock_demands) == 1
    assert mock_demands[0]['blood_type'] == 'O+'
    assert mock_demands[0]['status'] == 'Pending'

def test_cloned_repo__api__003_negative_unauthorized(client):
    """Unauthenticated user cannot create a blood demand.

    test_id: cloned_repo__api__003_negative_unauthorized
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    data = {
        'blood_type': 'O+',
        'units': '5',
        'document': (io.BytesIO(b'fake file content'), 'test.pdf')
    }
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')

    assert response.status_code == 302
    assert '/login/hospital' in response.location

def test_cloned_repo__api__004(client):
    """Home page is accessible.

    test_id: cloned_repo__api__004
    target: GET /
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/')
    # App redirects to login page if not logged in
    assert response.status_code == 302
    assert '/login/hospital' in response.location

def test_cloned_repo__api__005(client):
    """Hospital user can log in successfully.

    test_id: cloned_repo__api__005
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/hospital', data={'username': 'test_hospital', 'password': '123'})
    assert response.status_code == 302
    assert '/hospital/dashboard' in response.location
    with client.session_transaction() as sess:
        assert sess.get('role') == 'hospital'

def test_cloned_repo__api__005_negative_invalid_creds(client):
    """Hospital user cannot log in with invalid credentials.

    test_id: cloned_repo__api__005_negative_invalid_creds
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    # The app's logic only checks for presence, not correctness. So we send an empty password.
    response = client.post('/login/hospital', data={'username': 'test_hospital', 'password': ''})
    assert response.status_code == 200 # Renders login page again
    assert b'Invalid credentials.' in response.data
    with client.session_transaction() as sess:
        assert 'role' not in sess

def test_cloned_repo__api__006(client):
    """Admin user can log in successfully.

    test_id: cloned_repo__api__006
    target: POST /login/admin
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/admin', data={'username': 'test_admin', 'password': '123'})
    assert response.status_code == 302
    assert '/admin/queue' in response.location
    with client.session_transaction() as sess:
        assert sess.get('role') == 'admin'

def test_cloned_repo__api__007(client):
    """User can log out.

    test_id: cloned_repo__api__007
    target: GET /logout
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'

    response = client.get('/logout')
    assert response.status_code == 302
    assert '/login/hospital' in response.location
    with client.session_transaction() as sess:
        assert 'role' not in sess

def test_cloned_repo__api__008(client):
    """Authenticated hospital user can access their dashboard.

    test_id: cloned_repo__api__008
    target: GET /hospital/dashboard
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'

    response = client.get('/hospital/dashboard')
    assert response.status_code == 200
    assert b'Hospital Dashboard' in response.data

def test_cloned_repo__api__009(client):
    """Authenticated admin can access the demand queue.

    test_id: cloned_repo__api__009
    target: GET /admin/queue
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.get('/admin/queue')
    assert response.status_code == 200
    assert b'Verification Queue' in response.data

def test_cloned_repo__api__010(client):
    """Authenticated admin can access alerts.

    test_id: cloned_repo__api__010
    target: GET /admin/alerts
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.get('/admin/alerts')
    assert response.status_code == 200
    assert b'Alert Management' in response.data
