"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2024-05-29T17:18:04.123456Z
"""
import pytest
import io
from datetime import datetime
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_cloned_repo_api_001(client):
    """Verifies that the home page loads successfully for an anonymous user.

    test_id: cloned_repo__api__001
    target: GET /
    requirement_id: no requirement
    """
    response = client.get('/')
    assert response.status_code == 302
    assert '/login/hospital' in response.location

def test_cloned_repo_api_002(client):
    """Verifies a hospital user can log in successfully and is redirected.

    test_id: cloned_repo__api__002
    target: POST /login/hospital
    requirement_id: REQ-001
    """
    response = client.post('/login/hospital', data={
        'username': 'test_hospital',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Logged in to Hospital Portal successfully!' in response.data
    assert b'Hospital Dashboard' in response.data

def test_cloned_repo_api_003(client):
    """Verifies that an attempt to log in as an admin with wrong credentials fails and re-renders the login page.

    test_id: cloned_repo__api__003
    target: POST /login/admin
    requirement_id: REQ-001
    """
    response = client.post('/login/admin', data={
        'username': 'admin',
        'password': ''
    })
    assert response.status_code == 200
    assert b'Invalid credentials.' in response.data

def test_cloned_repo_api_004(client):
    """Verifies that protected hospital routes require authentication.

    test_id: cloned_repo__api__004
    target: GET /hospital/dashboard
    requirement_id: REQ-N-007
    """
    response = client.get('/hospital/dashboard')
    assert response.status_code == 302
    assert '/login/hospital' in response.location

def test_cloned_repo_api_005(client):
    """Verifies that protected admin routes require authentication.

    test_id: cloned_repo__api__005
    target: GET /admin/queue
    requirement_id: REQ-N-007
    """
    response = client.get('/admin/queue')
    assert response.status_code == 302
    assert '/login/admin' in response.location

def test_cloned_repo_api_006(client):
    """Verifies a logged-in hospital user can successfully submit a new demand request.

    test_id: cloned_repo__api__006
    target: POST /hospital/create-demand
    requirement_id: REQ-002,REQ-F-004
    """
    with client.session_transaction() as sess:
        sess['username'] = 'test_hospital'
        sess['role'] = 'hospital'

    form_data = {
        'blood_type': 'O+',
        'units': '5',
        'notes': 'Urgent request for surgery',
        'document': (io.BytesIO(b'fake compliance document'), 'compliance.pdf')
    }
    response = client.post('/hospital/create-demand', data=form_data, content_type='multipart/form-data')
    
    assert response.status_code == 302
    assert '/hospital/dashboard' in response.location

def test_cloned_repo_api_007(client):
    """Verifies a logged-in admin can successfully verify a pending demand.

    test_id: cloned_repo__api__007
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-003,REQ-F-006
    """
    with client.session_transaction() as sess:
        sess['username'] = 'test_admin'
        sess['role'] = 'admin'

    # Assuming demand with id=2 is in 'Pending' state from mock data
    demand_id_to_verify = 2
    response = client.post(f'/admin/verify/{demand_id_to_verify}', data={'action': 'approve'})
    
    assert response.status_code == 302
    assert '/admin/queue' in response.location

def test_cloned_repo_api_008(client):
    """Verifies that the logout endpoint correctly terminates the user session.

    test_id: cloned_repo__api__008
    target: GET /logout
    requirement_id: no requirement
    """
    # Log in first to establish a session
    client.post('/login/hospital', data={'username': 'test_user', 'password': 'pw'})

    # Then log out
    logout_response = client.get('/logout')
    assert logout_response.status_code == 302
    assert '/login/hospital' in logout_response.location

    # Verify session is cleared by accessing a protected route
    dashboard_response = client.get('/hospital/dashboard')
    assert dashboard_response.status_code == 302
    assert '/login/hospital' in dashboard_response.location

def test_cloned_repo_api_009(client):
    """Verifies that the admin audit log page is accessible to an authenticated admin.

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
