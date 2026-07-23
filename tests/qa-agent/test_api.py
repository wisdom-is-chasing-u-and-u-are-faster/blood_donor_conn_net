"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2024-07-25T17:09:47.411641Z
"""
import pytest
import io
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for form tests
    with app.test_client() as client:
        yield client

def test_get_home_redirects(client):
    """Verifies that the home page redirects to the login page when not authenticated.

    test_id: cloned_repo__api__001
    target: GET /
    requirement_id: no requirement
    """
    response = client.get('/')
    assert response.status_code == 302
    assert '/login/hospital' in response.location

def test_post_login_hospital_valid_redirects(client):
    """Tests that a valid hospital login redirects to the dashboard.

    test_id: cloned_repo__api__002
    target: POST /login/hospital
    requirement_id: REQ-001
    """
    response = client.post('/login/hospital', data={
        'username': 'test_hospital',
        'password': 'password123'
    }, follow_redirects=False)
    assert response.status_code == 302
    assert '/hospital/dashboard' in response.location

def test_post_login_hospital_invalid_fails(client):
    """Tests that an invalid hospital login re-renders the login page with an error.

    test_id: cloned_repo__api__003
    target: POST /login/hospital
    requirement_id: REQ-001
    """
    response = client.post('/login/hospital', data={
        'username': 'baduser',
        'password': ''
    })
    assert response.status_code == 200
    assert b'Invalid credentials.' in response.data

def test_post_login_admin_valid_redirects(client):
    """Tests that a valid admin login redirects to the admin queue.

    test_id: cloned_repo__api__004
    target: POST /login/admin
    requirement_id: REQ-001
    """
    response = client.post('/login/admin', data={
        'username': 'test_admin',
        'password': 'password123'
    }, follow_redirects=False)
    assert response.status_code == 302
    assert '/admin/queue' in response.location

def test_get_hospital_dashboard_requires_auth(client):
    """Verifies that the hospital dashboard redirects to login when not authenticated.

    test_id: cloned_repo__api__005
    target: GET /hospital/dashboard
    requirement_id: REQ-N-007
    """
    response = client.get('/hospital/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login/hospital' in response.location

def test_post_hospital_create_demand_succeeds(client):
    """Verifies an authenticated hospital user can create a blood demand.

    test_id: cloned_repo__api__006
    target: POST /hospital/create-demand
    requirement_id: REQ-002,REQ-F-004,REQ-F-005
    """
    with client.session_transaction() as sess:
        sess['username'] = 'test_hospital'
        sess['role'] = 'hospital'

    data = {
        'blood_type': 'O+',
        'units': '3',
        'document': (io.BytesIO(b'fake document content'), 'compliance.pdf'),
        'notes': 'Urgent request'
    }
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data', follow_redirects=False)
    
    assert response.status_code == 302
    assert '/hospital/dashboard' in response.location

def test_post_admin_verify_succeeds_for_admin(client):
    """Verifies an admin can approve a pending demand.

    test_id: cloned_repo__api__007
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-003,REQ-F-006
    """
    with client.session_transaction() as sess:
        sess['username'] = 'test_admin'
        sess['role'] = 'admin'

    # Assuming demand with id=2 is 'Pending' from mock data
    demand_id_to_verify = 2
    response = client.post(f'/admin/verify/{demand_id_to_verify}', data={'action': 'approve'}, follow_redirects=False)

    assert response.status_code == 302
    assert '/admin/queue' in response.location

def test_post_admin_verify_forbidden_for_hospital(client):
    """Verifies a hospital user cannot access the admin verification endpoint.

    test_id: cloned_repo__api__008
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-001
    """
    with client.session_transaction() as sess:
        sess['username'] = 'test_hospital'
        sess['role'] = 'hospital'

    demand_id_to_verify = 2
    response = client.post(f'/admin/verify/{demand_id_to_verify}', data={'action': 'approve'}, follow_redirects=False)

    # The app redirects unauthorized users to the admin login page
    assert response.status_code == 302
    assert '/login/admin' in response.location

def test_get_admin_audit_log_requires_admin_auth(client):
    """Verifies the audit log is accessible to an authenticated admin.

    test_id: cloned_repo__api__009
    target: GET /admin/audit-log
    requirement_id: REQ-003,REQ-F-006
    """
    with client.session_transaction() as sess:
        sess['username'] = 'test_admin'
        sess['role'] = 'admin'

    response = client.get('/admin/audit-log')

    assert response.status_code == 200
    assert b'Audit Log' in response.data
    assert b'SYSTEM STARTUP' in response.data # Check for content from mock data
