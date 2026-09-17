"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2024-07-12T11:46:01.300501Z
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

def test_create_demand_with_valid_data_returns_success(client):
    """POST /hospital/create-demand with valid data returns success.

    test_id: cloned_repo__api__001
    target: POST /hospital/create-demand
    requirement_id: REQ-F-001,REQ-F-007
    ac_ids: REQ-F-001-AC-1,REQ-F-007-AC-1
    """
    with client.session_transaction() as sess:
        sess['username'] = 'testhospital'
        sess['role'] = 'hospital'
    
    data = {
        'blood_type': 'O+',
        'units': '2',
        'location': 'Test Location',
        'document': (io.BytesIO(b'compliance doc'), 'test.pdf')
    }
    
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 302
    assert '/hospital/dashboard' in response.location

def test_create_demand_with_invalid_data_returns_error(client):
    """POST /hospital/create-demand with invalid data returns error.

    test_id: cloned_repo__api__001_negative_invalid_input
    target: POST /hospital/create-demand
    requirement_id: REQ-F-001
    ac_ids: REQ-F-001-AC-1
    """
    with client.session_transaction() as sess:
        sess['username'] = 'testhospital'
        sess['role'] = 'hospital'

    # Missing 'units' and 'document'
    data = {'blood_type': 'O+'}
    
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')
    
    # The code redirects back to the form page on validation failure
    assert response.status_code == 302
    assert '/hospital/create-demand' in response.location
    
    # Check for flash message indicating an error
    with client.session_transaction() as sess:
        flashes = sess.get('_flashes', [])
        assert any('required' in message[1] for message in flashes)

def test_login_admin_with_valid_credentials_grants_access(client):
    """POST /login/admin with valid credentials grants access.

    test_id: cloned_repo__api__002
    target: POST /login/admin
    requirement_id: CONSTRAINT-016
    ac_ids: CONSTRAINT-016-AC-2
    """
    response = client.post('/login/admin', data={'username': 'admin', 'password': 'valid_password'})
    
    assert response.status_code == 302
    assert '/admin/queue' in response.location
    with client.session_transaction() as sess:
        assert sess.get('role') == 'admin'
        assert sess.get('username') == 'admin'

def test_login_admin_with_invalid_credentials_denies_access(client):
    """POST /login/admin with invalid credentials denies access.

    test_id: cloned_repo__api__002_negative_auth_failure
    target: POST /login/admin
    requirement_id: CONSTRAINT-016
    ac_ids: CONSTRAINT-016-AC-2
    """
    # The code's logic only checks if username and password are not empty.
    # Sending an empty password will trigger the failure case.
    response = client.post('/login/admin', data={'username': 'admin', 'password': ''})
    
    # The app re-renders the login page with a flash message, so status is 200.
    assert response.status_code == 200
    assert b'Invalid credentials.' in response.data

def test_admin_audit_log_returns_audit_log_page_for_authenticated_admin(client):
    """GET /admin/audit-log returns audit log page for authenticated admin.

    test_id: cloned_repo__api__003
    target: GET /admin/audit-log
    requirement_id: CONSTRAINT-016
    ac_ids: CONSTRAINT-016-AC-1
    """
    with client.session_transaction() as sess:
        sess['username'] = 'admin'
        sess['role'] = 'admin'
        
    response = client.get('/admin/audit-log')
    
    assert response.status_code == 200
    assert b'Audit Log' in response.data

def test_get_returns_home_page(client):
    """GET / returns home page.

    test_id: cloned_repo__api__004_orphan
    target: GET /
    requirement_id: no requirement
    ac_ids: none
    """
    # The home route redirects to a login page if not authenticated.
    response = client.get('/')
    assert response.status_code == 302
    assert '/login/hospital' in response.location

def test_login_hospital_with_valid_credentials_grants_access(client):
    """POST /login/hospital with valid credentials grants access.

    test_id: cloned_repo__api__005_orphan
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/hospital', data={'username': 'hospital', 'password': 'valid_password'})
    
    assert response.status_code == 302
    assert '/hospital/dashboard' in response.location
    with client.session_transaction() as sess:
        assert sess.get('role') == 'hospital'

def test_logout_redirects_to_home_page(client):
    """GET /logout redirects to home page.

    test_id: cloned_repo__api__006_orphan
    target: GET /logout
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
        sess['role'] = 'hospital'
        
    response = client.get('/logout')
    
    assert response.status_code == 302
    assert '/login/hospital' in response.location
    
    # Verify session is cleared by making a subsequent request to a protected route
    response_after_logout = client.get('/hospital/dashboard')
    assert response_after_logout.status_code == 302
    assert '/login/hospital' in response_after_logout.location

def test_admin_queue_requires_admin_authentication(client):
    """GET /admin/queue requires admin authentication.

    test_id: cloned_repo__api__007_orphan
    target: GET /admin/queue
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/admin/queue')
    
    # Expect redirect to admin login page
    assert response.status_code == 302
    assert '/login/admin' in response.location

def test_admin_verify_demand_successfully_verifies_a_demand(client, monkeypatch):
    """POST /admin/verify/<int:demand_id> successfully verifies a demand.

    test_id: cloned_repo__api__008_orphan
    target: POST /admin/verify/<int:demand_id>
    requirement_id: no requirement
    ac_ids: none
    """
    # Mock the in-memory database
    mock_demands = [{
        "id": 123,
        "hospital": "Test Hospital",
        "blood_type": "A+",
        "units": 5,
        "filename": "doc.pdf",
        "status": "Pending"
    }]
    monkeypatch.setattr('app.demands', mock_demands)

    with client.session_transaction() as sess:
        sess['username'] = 'admin'
        sess['role'] = 'admin'
        
    response = client.post('/admin/verify/123', data={'action': 'approve'})
    
    assert response.status_code == 302
    assert '/admin/queue' in response.location
    
    # Verify the status was updated in our mock list
    assert mock_demands[0]['status'] == 'Approved'
