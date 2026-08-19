"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2024-07-31T16:08:44.000Z
"""
import pytest
from app import app
import io
import copy

# In-memory data from app.py, to reset state for each test
from app import demands as app_demands, audit_logs as app_audit_logs, alerts as app_alerts, scheduled_donors as app_scheduled_donors

original_demands = copy.deepcopy(app_demands)
original_audit_logs = copy.deepcopy(app_audit_logs)
original_alerts = copy.deepcopy(app_alerts)
original_scheduled_donors = copy.deepcopy(app_scheduled_donors)

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def reset_app_state():
    """Resets the in-memory 'database' before each test run."""
    global app_demands, app_audit_logs, app_alerts, app_scheduled_donors
    app_demands[:] = copy.deepcopy(original_demands)
    app_audit_logs[:] = copy.deepcopy(original_audit_logs)
    app_alerts[:] = copy.deepcopy(original_alerts)
    app_scheduled_donors[:] = copy.deepcopy(original_scheduled_donors)
    yield

def test_admin_can_approve_hospital_request(client):
    """Verify admin can approve a hospital request.

    test_id: cloned_repo__api__001
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'
    
    # There is a pending demand with id=2 in the initial data
    response = client.post('/admin/verify/2', data={'action': 'approve'}, follow_redirects=True)
    assert response.status_code == 200
    # After approval, the pending demand should be gone from the queue page
    assert b'id="demand-2"' not in response.data

def test_admin_can_retrieve_audit_log(client):
    """Verify admin can retrieve the audit log.

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
    assert b'SYSTEM STARTUP' in response.data
    assert b'HOSPITAL DEMAND APPROVED' in response.data

def test_hospital_can_create_demand_request(client):
    """Verify authenticated hospital can create a demand request.

    test_id: cloned_repo__api__003
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'
    data = {
        'blood_type': 'AB-',
        'units': '3',
        'notes': 'Urgent test case',
        'document': (io.BytesIO(b"mock file content"), 'test_doc.pdf')
    }
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')
    assert response.status_code == 302
    assert response.location == '/hospital/dashboard'

def test_unauthenticated_cannot_create_demand(client):
    """Verify unauthenticated user cannot create a hospital demand.

    test_id: cloned_repo__api__003_negative_unauthenticated
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    data = {
        'blood_type': 'AB-',
        'units': '3',
        'document': (io.BytesIO(b"mock file content"), 'test_doc.pdf')
    }
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')
    assert response.status_code == 302
    assert response.location == '/login/hospital'

def test_home_page_is_accessible(client):
    """Verify home page is accessible.

    test_id: cloned_repo__api__004
    target: GET /
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/')
    # For unauthenticated users, it redirects to the login page
    assert response.status_code == 302
    assert response.location == '/login/hospital'

def test_hospital_login_page_is_accessible(client):
    """Verify hospital login page is accessible.

    test_id: cloned_repo__api__005
    target: GET /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/login/hospital')
    assert response.status_code == 200
    assert b'Hospital Portal' in response.data

def test_hospital_user_can_log_in(client):
    """Verify hospital user can log in.

    test_id: cloned_repo__api__006
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/hospital', data={'username': 'testuser', 'password': 'password'})
    assert response.status_code == 302
    assert response.location == '/hospital/dashboard'

def test_admin_login_page_is_accessible(client):
    """Verify admin login page is accessible.

    test_id: cloned_repo__api__007
    target: GET /login/admin
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/login/admin')
    assert response.status_code == 200
    assert b'Administrator Portal' in response.data

def test_admin_user_can_log_in(client):
    """Verify admin user can log in.

    test_id: cloned_repo__api__008
    target: POST /login/admin
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/admin', data={'username': 'testadmin', 'password': 'password'})
    assert response.status_code == 302
    assert response.location == '/admin/queue'

def test_user_can_log_out(client):
    """Verify user can log out.

    test_id: cloned_repo__api__009
    target: GET /logout
    requirement_id: no requirement
    ac_ids: none
    """
    # First, log in to establish a session
    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'
    
    response = client.get('/logout')
    assert response.status_code == 302
    assert response.location == '/login/hospital'

    # Verify session is cleared by trying to access a protected route
    response_after_logout = client.get('/hospital/dashboard', follow_redirects=True)
    assert response_after_logout.status_code == 200
    assert b'Please log in first' in response_after_logout.data

def test_authenticated_hospital_can_access_dashboard(client):
    """Verify authenticated hospital user can access dashboard.

    test_id: cloned_repo__api__010
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

def test_authenticated_admin_can_access_demand_queue(client):
    """Verify authenticated admin can access demand queue.

    test_id: cloned_repo__api__011
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

def test_authenticated_admin_can_access_alerts_page(client):
    """Verify authenticated admin can access alerts page.

    test_id: cloned_repo__api__012
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
