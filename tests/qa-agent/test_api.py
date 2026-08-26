"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2024-07-25T17:39:09.610816
"""
import pytest
from app import app
import io

@pytest.fixture
def client():
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False, # Disable CSRF for testing forms
        "SECRET_KEY": "test-secret-key"
    })
    with app.test_client() as client:
        yield client

def test_verify_POST_admin_verify_int_demand_id_returns_success(client, monkeypatch):
    """Verify POST /admin/verify/<int:demand_id> returns success.

    test_id: cloned_repo__api__001
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    mock_demands = [
        {"id": 1, "status": "Approved"},
        {"id": 2, "status": "Pending", "hospital": "TestHosp", "blood_type": "O-"}
    ]
    monkeypatch.setattr("app.demands", mock_demands)
    monkeypatch.setattr("app.alerts", [])

    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.post('/admin/verify/2', data={'action': 'approve'}, follow_redirects=False)

    assert response.status_code == 302
    assert response.location == '/admin/queue'
    assert mock_demands[1]['status'] == 'Approved'

def test_verify_GET_admin_audit_log_returns_audit_data(client, monkeypatch):
    """Verify GET /admin/audit-log returns audit data.

    test_id: cloned_repo__api__002
    target: GET /admin/audit-log
    requirement_id: REQ-N-012
    ac_ids: REQ-N-012-AC-1
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'

    response = client.get('/admin/audit-log')

    assert response.status_code == 200
    assert b'Audit Log' in response.data
    assert b'SYSTEM STARTUP' in response.data

def test_verify_POST_hospital_create_demand_successfully_creates_a_demand(client, monkeypatch):
    """Verify POST /hospital/create-demand successfully creates a demand.

    test_id: cloned_repo__api__003
    target: POST /hospital/create-demand
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    mock_demands = []
    monkeypatch.setattr("app.demands", mock_demands)

    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'

    data = {
        'blood_type': 'B+',
        'units': '3',
        'document': (io.BytesIO(b'test file data'), 'test.pdf')
    }
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')

    assert response.status_code == 302
    assert response.location == '/hospital/dashboard'
    assert len(mock_demands) == 1
    assert mock_demands[0]['blood_type'] == 'B+'
    assert mock_demands[0]['status'] == 'Pending'

def test_verify_POST_hospital_create_demand_fails_without_authentication(client):
    """Verify POST /hospital/create-demand fails without authentication.

    test_id: cloned_repo__api__004_negative_unauthenticated
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    response = client.post('/hospital/create-demand', data={})
    assert response.status_code == 302
    assert response.location == '/login/hospital'

def test_verify_GET_returns_200_OK(client):
    """Verify GET / returns a redirect for unauthenticated users.

    test_id: cloned_repo__api__005
    target: GET /
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/')
    assert response.status_code == 302
    assert response.location == '/login/hospital'

def test_verify_GET_login_hospital_returns_login_page(client):
    """Verify GET /login/hospital returns login page.

    test_id: cloned_repo__api__006
    target: GET /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/login/hospital')
    assert response.status_code == 200
    assert b'Hospital Portal Login' in response.data

def test_verify_POST_login_hospital_with_valid_credentials_redirects(client):
    """Verify POST /login/hospital with valid credentials redirects.

    test_id: cloned_repo__api__007
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/hospital', data={'username': 'testuser', 'password': 'password'})
    assert response.status_code == 302
    assert response.location == '/hospital/dashboard'

def test_verify_POST_login_hospital_with_invalid_credentials_shows_error(client):
    """Verify POST /login/hospital with invalid credentials shows error.

    test_id: cloned_repo__api__008_negative_bad_creds
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/hospital', data={'username': '', 'password': ''})
    assert response.status_code == 200
    assert b'Invalid credentials.' in response.data

def test_verify_GET_login_admin_returns_admin_login_page(client):
    """Verify GET /login/admin returns admin login page.

    test_id: cloned_repo__api__009
    target: GET /login/admin
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/login/admin')
    assert response.status_code == 200
    assert b'Administrator Portal Login' in response.data

def test_verify_GET_logout_redirects_successfully(client):
    """Verify GET /logout redirects successfully.

    test_id: cloned_repo__api__010
    target: GET /logout
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
        sess['role'] = 'hospital'
    
    response = client.get('/logout')
    assert response.status_code == 302
    assert response.location == '/login/hospital'

def test_verify_GET_hospital_dashboard_is_accessible_when_authenticated(client):
    """Verify GET /hospital/dashboard is accessible when authenticated.

    test_id: cloned_repo__api__011
    target: GET /hospital/dashboard
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'

    response = client.get('/hospital/dashboard')
    assert response.status_code == 200
    assert b'Hospital Dashboard' in response.data

def test_verify_GET_admin_queue_is_accessible_by_admin(client):
    """Verify GET /admin/queue is accessible by admin.

    test_id: cloned_repo__api__012
    target: GET /admin/queue
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'

    response = client.get('/admin/queue')
    assert response.status_code == 200
    assert b'Verification Queue' in response.data
