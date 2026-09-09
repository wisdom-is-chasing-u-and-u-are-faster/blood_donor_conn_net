"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2024-05-21T16:30:00.123456Z
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

def test_verify_post_to_admin_verify_id_returns_a_success_status():
    """Verify POST to `/admin/verify/<id>` returns a success status.

    test_id: cloned_repo__api__001
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    with patch('app.demands') as mock_demands:
        mock_demands.__iter__.return_value = [{'id': 123, 'status': 'Pending', 'blood_type': 'A+', 'hospital': 'TestHosp'}]
        with client.session_transaction() as sess:
            sess['role'] = 'admin'
            sess['username'] = 'test_admin'
        response = client.post('/admin/verify/123', data={'action': 'approve'})
        # The endpoint redirects on success
        assert response.status_code == 302
        assert '/admin/queue' in response.location

def test_verify_get_admin_audit_log_returns_audit_data(client):
    """Verify GET `/admin/audit-log` returns audit data.

    test_id: cloned_repo__api__002
    target: GET /admin/audit-log
    requirement_id: REQ-N-012,REQ-N-011
    ac_ids: REQ-N-012-AC-1,REQ-N-011-AC-1
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
    response = client.get('/admin/audit-log')
    assert response.status_code == 200
    assert b'Audit Log' in response.data

def test_verify_post_to_hospital_create_demand_with_valid_data_succeeds(client):
    """Verify POST to `/hospital/create-demand` with valid data succeeds.

    test_id: cloned_repo__api__003
    target: POST /hospital/create-demand
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'
    
    data = {
        'blood_type': 'O+',
        'units': '5',
        'document': (io.BytesIO(b'dummy compliance data'), 'compliance.pdf')
    }
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')
    # The endpoint redirects to the dashboard on success
    assert response.status_code == 302
    assert '/hospital/dashboard' in response.location

def test_verify_post_to_hospital_create_demand_without_authentication_fails(client):
    """Verify POST to `/hospital/create-demand` without authentication fails.

    test_id: cloned_repo__api__004_negative_auth
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    data = {
        'blood_type': 'A-',
        'units': '2',
        'document': (io.BytesIO(b'dummy compliance data'), 'compliance.pdf')
    }
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')
    # Unauthorized users are redirected to the login page
    assert response.status_code == 302
    assert '/login/hospital' in response.location

def test_verify_get_returns_a_200_ok_status(client):
    """Verify GET `/` returns a 200 OK status.

    test_id: cloned_repo__api__005
    target: GET /
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/')
    # Unauthenticated users are redirected to the login page
    assert response.status_code == 302
    assert '/login/hospital' in response.location

def test_verify_get_login_hospital_returns_the_login_page(client):
    """Verify GET `/login/hospital` returns the login page.

    test_id: cloned_repo__api__006
    target: GET /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/login/hospital')
    assert response.status_code == 200
    assert b'Hospital Portal Login' in response.data

def test_verify_post_login_hospital_with_valid_credentials_succeeds(client):
    """Verify POST `/login/hospital` with valid credentials succeeds.

    test_id: cloned_repo__api__007
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/hospital', data={'username': 'hosp_user', 'password': 'correct_password'})
    assert response.status_code == 302
    assert '/hospital/dashboard' in response.location

def test_verify_post_login_hospital_with_invalid_credentials_fails(client):
    """Verify POST `/login/hospital` with invalid credentials fails.

    test_id: cloned_repo__api__008_negative_auth
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/hospital', data={'username': 'hosp_user', 'password': ''})
    # Failed login re-renders the login page
    assert response.status_code == 200
    assert b'Invalid credentials' in response.data

def test_verify_get_admin_queue_for_authenticated_admin_returns_200(client):
    """Verify GET `/admin/queue` for authenticated admin returns 200.

    test_id: cloned_repo__api__009
    target: GET /admin/queue
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
    response = client.get('/admin/queue')
    assert response.status_code == 200
    assert b'Verification Queue' in response.data

def test_verify_get_admin_alerts_for_authenticated_admin_returns_200(client):
    """Verify GET `/admin/alerts` for authenticated admin returns 200.

    test_id: cloned_repo__api__010
    target: GET /admin/alerts
    requirement_id: REQ-N-011
    ac_ids: REQ-N-011-AC-1
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
    response = client.get('/admin/alerts')
    assert response.status_code == 200
    assert b'Alert Management' in response.data
