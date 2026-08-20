import pytest
from unittest.mock import patch
import io
import datetime

# It's a good practice to import the app and then configure it for testing
# before any tests run. The client fixture will handle this.
from app import app


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        yield client


def test_cloned_repo_api_001(client, monkeypatch):
    """Verify an admin can approve a demand request via API.

    test_id: cloned_repo__api__001
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    mock_demands = [
        {"id": 123, "hospital": "Test Hosp", "blood_type": "O-", "units": 4, "filename": "doc.pdf", "status": "Pending"}
    ]
    monkeypatch.setattr('app.demands', mock_demands)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.post('/admin/verify/123', data={'action': 'approve'})

    assert response.status_code == 302
    assert response.location == '/admin/queue'
    assert app.demands[0]['status'] == 'Approved'


def test_cloned_repo_api_002(client):
    """Verify the admin audit log endpoint is accessible.

    test_id: cloned_repo__api__002
    target: GET /admin/audit-log
    requirement_id: REQ-N-012,REQ-N-011
    ac_ids: REQ-N-012-AC-1,REQ-N-011-AC-1
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.get('/admin/audit-log')

    assert response.status_code == 200
    assert b'Audit Log' in response.data


def test_cloned_repo_api_003(client, monkeypatch):
    """Verify an authenticated hospital can create a demand request.

    test_id: cloned_repo__api__003
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    initial_demands = []
    monkeypatch.setattr('app.demands', initial_demands)

    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'

    post_data = {
        'blood_type': 'O+',
        'units': '5',
        'document': (io.BytesIO(b'fake file contents'), 'test.pdf')
    }

    response = client.post('/hospital/create-demand', data=post_data, content_type='multipart/form-data')

    assert response.status_code == 302
    assert response.location == '/hospital/dashboard'
    assert len(app.demands) == 1
    assert app.demands[0]['blood_type'] == 'O+'
    assert app.demands[0]['units'] == 5
    assert app.demands[0]['status'] == 'Pending'


def test_cloned_repo_api_004_negative_unauthenticated(client):
    """Verify creating a demand request fails for unauthenticated users.

    test_id: cloned_repo__api__004_negative_unauthenticated
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    post_data = {
        'blood_type': 'A-',
        'units': '2',
        'document': (io.BytesIO(b'fake file contents'), 'test.pdf')
    }
    response = client.post('/hospital/create-demand', data=post_data, content_type='multipart/form-data')

    assert response.status_code == 302
    assert response.location == '/login/hospital'


def test_cloned_repo_api_005(client):
    """Verify home page is accessible.

    test_id: cloned_repo__api__005
    target: GET /
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/')
    assert response.status_code == 302
    assert response.location == '/login/hospital'


def test_cloned_repo_api_006(client):
    """Verify hospital login page is accessible.

    test_id: cloned_repo__api__006
    target: GET /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/login/hospital')
    assert response.status_code == 200
    assert b'Hospital Portal Login' in response.data


def test_cloned_repo_api_007(client):
    """Verify hospital user can log in with valid credentials.

    test_id: cloned_repo__api__007
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/hospital', data={'username': 'hospital_user', 'password': 'correct_password'})
    assert response.status_code == 302
    assert response.location == '/hospital/dashboard'


def test_cloned_repo_api_008_negative_invalid_creds(client):
    """Verify hospital login fails with invalid credentials.

    test_id: cloned_repo__api__008_negative_invalid_creds
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    # The app's logic considers any non-empty username/password as valid.
    # To trigger failure, we send empty credentials.
    response = client.post('/login/hospital', data={'username': '', 'password': ''})
    assert response.status_code == 200
    assert b'Invalid credentials' in response.data


def test_cloned_repo_api_009(client):
    """Verify admin login page is accessible.

    test_id: cloned_repo__api__009
    target: GET /login/admin
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/login/admin')
    assert response.status_code == 200
    assert b'Administrator Portal Login' in response.data


def test_cloned_repo_api_010(client):
    """Verify admin user can log in with valid credentials.

    test_id: cloned_repo__api__010
    target: POST /login/admin
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/admin', data={'username': 'admin_user', 'password': 'correct_password'})
    assert response.status_code == 302
    assert response.location == '/admin/queue'


def test_cloned_repo_api_011(client):
    """Verify user can log out.

    test_id: cloned_repo__api__011
    target: GET /logout
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_user'

    response = client.get('/logout')
    assert response.status_code == 302
    assert response.location == '/login/hospital'

    # Verify session is cleared by trying to access a protected route
    dashboard_response = client.get('/hospital/dashboard')
    assert dashboard_response.status_code == 302
    assert dashboard_response.location == '/login/hospital'


def test_cloned_repo_api_012_negative_unauthenticated(client):
    """Verify hospital dashboard is protected from unauthenticated access.

    test_id: cloned_repo__api__012_negative_unauthenticated
    target: GET /hospital/dashboard
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/hospital/dashboard')
    assert response.status_code == 302
    assert response.location == '/login/hospital'


def test_cloned_repo_api_013(client):
    """Verify create demand page is accessible.

    test_id: cloned_repo__api__013
    target: GET /hospital/create-demand
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'

    response = client.get('/hospital/create-demand')
    assert response.status_code == 200
    assert b'Create New Blood Demand' in response.data


def test_cloned_repo_api_014_negative_unauthenticated(client):
    """Verify admin queue is protected from unauthenticated access.

    test_id: cloned_repo__api__014_negative_unauthenticated
    target: GET /admin/queue
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/admin/queue')
    assert response.status_code == 302
    assert response.location == '/login/admin'


def test_cloned_repo_api_015_negative_unauthenticated(client):
    """Verify admin alerts page is protected from unauthenticated access.

    test_id: cloned_repo__api__015_negative_unauthenticated
    target: GET /admin/alerts
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/admin/alerts')
    assert response.status_code == 302
    assert response.location == '/login/admin'
