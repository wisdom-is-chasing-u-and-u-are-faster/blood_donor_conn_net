"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2024-07-12T19:47:39.123456Z
"""

import pytest
import io
from unittest.mock import patch
from app import app

@pytest.fixture
def client():
    """A test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def isolated_app_data(monkeypatch):
    """Fixture to reset in-memory data for each test to ensure isolation."""
    initial_demands = [
        {"id": 1, "hospital": "General Hospital", "blood_type": "A+", "units": 10, "filename": "compliance_doc_A.pdf", "status": "Approved"},
        {"id": 2, "hospital": "General Hospital", "blood_type": "O-", "units": 4, "filename": "compliance_doc_B.pdf", "status": "Pending"}
    ]
    initial_alerts = [
        {"id": 1, "hospital": "General Hospital", "blood_type": "A+", "status": "Active"}
    ]
    initial_audit_logs = [
        {"action": "SYSTEM STARTUP", "details": "BDCN Core Platform service started successfully.", "user": "System", "timestamp": "2023-01-01 12:00:00"}
    ]

    monkeypatch.setattr('app.demands', initial_demands)
    monkeypatch.setattr('app.alerts', initial_alerts)
    monkeypatch.setattr('app.audit_logs', initial_audit_logs)

@pytest.fixture
def admin_client(client):
    """A test client pre-authenticated as an admin user."""
    with client.session_transaction() as sess:
        sess['username'] = 'test_admin'
        sess['role'] = 'admin'
    yield client

@pytest.fixture
def hospital_client(client):
    """A test client pre-authenticated as a hospital user."""
    with client.session_transaction() as sess:
        sess['username'] = 'test_hospital'
        sess['role'] = 'hospital'
    yield client

def test_verify_demand_with_valid_admin_credentials(admin_client):
    """An authenticated admin can successfully verify a demand.

    test_id: cloned_repo__api__001
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017,REQ-F-001
    ac_ids: REQ-F-017-AC-1,REQ-F-001-AC-1
    """
    response = admin_client.post('/admin/verify/2', data={'action': 'approve'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Approved demand #2!' in response.data

def test_fail_to_verify_demand_without_authentication(client):
    """An unauthenticated user cannot verify a demand and is redirected.

    test_id: cloned_repo__api__002_negative_unauthorized
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017,REQ-F-001
    ac_ids: REQ-F-017-AC-1,REQ-F-001-AC-1
    """
    response = client.post('/admin/verify/1', data={'action': 'approve'})
    assert response.status_code == 302
    assert '/login/admin' in response.location

def test_fail_to_verify_a_non_existent_demand(admin_client):
    """The API returns a message when trying to verify a non-existent demand.

    test_id: cloned_repo__api__003_negative_not_found
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017,REQ-F-001
    ac_ids: REQ-F-017-AC-1,REQ-F-001-AC-1
    """
    response = admin_client.post('/admin/verify/99999', data={'action': 'approve'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Demand request not found.' in response.data

def test_fetch_audit_log_with_admin_credentials(admin_client):
    """An authenticated admin can successfully retrieve the audit log.

    test_id: cloned_repo__api__004
    target: GET /admin/audit-log
    requirement_id: REQ-N-012,REQ-N-011
    ac_ids: REQ-N-012-AC-1,REQ-N-011-AC-1
    """
    response = admin_client.get('/admin/audit-log')
    assert response.status_code == 200
    assert b'Audit Log' in response.data
    assert b'SYSTEM STARTUP' in response.data

def test_fail_to_fetch_audit_log_without_admin_credentials(client):
    """A non-admin user is redirected from the audit log page.

    test_id: cloned_repo__api__005_negative_unauthorized
    target: GET /admin/audit-log
    requirement_id: REQ-N-012
    ac_ids: REQ-N-012-AC-1
    """
    response = client.get('/admin/audit-log')
    assert response.status_code == 302
    assert '/login/admin' in response.location

def test_fetch_hospital_dashboard_with_valid_credentials(hospital_client):
    """An authenticated hospital user can view their dashboard.

    test_id: cloned_repo__api__006
    target: GET /hospital/dashboard
    requirement_id: REQ-N-004
    ac_ids: REQ-N-004-AC-1
    """
    response = hospital_client.get('/hospital/dashboard')
    assert response.status_code == 200
    assert b'Current Blood Demands' in response.data

def test_create_a_new_hospital_demand_with_valid_authentication(hospital_client):
    """An authenticated hospital user can submit a new demand.

    test_id: cloned_repo__api__007
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    data = {
        'blood_type': 'A-',
        'units': '5',
        'notes': 'Urgent',
        'document': (io.BytesIO(b'mock file content'), 'compliance.pdf')
    }
    response = hospital_client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')
    assert response.status_code == 302
    assert '/hospital/dashboard' in response.location

def test_fail_to_create_hospital_demand_without_authentication(client):
    """An unauthenticated user cannot create a new demand.

    test_id: cloned_repo__api__008_negative_unauthorized
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    data = {'blood_type': 'A-', 'quantity': '1'}
    response = client.post('/hospital/create-demand', data=data)
    assert response.status_code == 302
    assert '/login/hospital' in response.location

def test_fail_to_create_hospital_demand_with_invalid_data(hospital_client):
    """The API rejects creating a demand with missing data.

    test_id: cloned_repo__api__009_negative_invalid_input
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    data = {'quantity': '1'} # Missing blood_type and document
    response = hospital_client.post('/hospital/create-demand', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'All fields including compliance document upload are required.' in response.data

def test_verify_home_page_is_accessible(client):
    """The root endpoint redirects to the hospital login page.

    test_id: cloned_repo__api__010
    target: GET /
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/')
    assert response.status_code == 302
    assert '/login/hospital' in response.location

def test_verify_hospital_login_page_is_accessible(client):
    """The GET endpoint for the hospital login page returns a successful response.

    test_id: cloned_repo__api__011
    target: GET /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/login/hospital')
    assert response.status_code == 200
    assert b'Hospital Portal Login' in response.data

def test_perform_hospital_login_with_valid_credentials(client):
    """A user can log in as a hospital and is redirected to the dashboard.

    test_id: cloned_repo__api__012
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/hospital', data={'username': 'hospital_user', 'password': 'password'})
    assert response.status_code == 302
    assert '/hospital/dashboard' in response.location

def test_fail_hospital_login_with_invalid_credentials(client):
    """A user cannot log in as a hospital with missing credentials.

    test_id: cloned_repo__api__013_negative_bad_creds
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/hospital', data={'username': 'hospital_user', 'password': ''}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid credentials.' in response.data

def test_verify_admin_login_page_is_accessible(client):
    """The GET endpoint for the admin login page returns a successful response.

    test_id: cloned_repo__api__014
    target: GET /login/admin
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/login/admin')
    assert response.status_code == 200
    assert b'Administrator Portal Login' in response.data

def test_perform_admin_login_with_valid_credentials(client):
    """A user can log in as an admin and is redirected to the admin queue.

    test_id: cloned_repo__api__015
    target: POST /login/admin
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/admin', data={'username': 'admin_user', 'password': 'password'})
    assert response.status_code == 302
    assert '/admin/queue' in response.location

def test_fail_admin_login_with_invalid_credentials(client):
    """A user cannot log in as an admin with missing credentials.

    test_id: cloned_repo__api__016_negative_bad_creds
    target: POST /login/admin
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/admin', data={'username': 'admin_user', 'password': ''}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid credentials.' in response.data

def test_verify_logout_functionality(admin_client):
    """The logout endpoint clears the session and redirects.

    test_id: cloned_repo__api__017
    target: GET /logout
    requirement_id: no requirement
    ac_ids: none
    """
    response = admin_client.get('/logout')
    assert response.status_code == 302
    assert '/login/hospital' in response.location
    # Verify session is cleared by trying to access an authenticated page
    response_after_logout = admin_client.get('/admin/queue')
    assert response_after_logout.status_code == 302
    assert '/login/admin' in response_after_logout.location

def test_verify_create_demand_page_is_accessible(hospital_client):
    """The create demand page is accessible to an authenticated hospital user.

    test_id: cloned_repo__api__018
    target: GET /hospital/create-demand
    requirement_id: no requirement
    ac_ids: none
    """
    response = hospital_client.get('/hospital/create-demand')
    assert response.status_code == 200
    assert b'Create New Blood Demand' in response.data

def test_verify_admin_queue_page_is_accessible(admin_client):
    """The admin queue page is accessible to an authenticated admin.

    test_id: cloned_repo__api__019
    target: GET /admin/queue
    requirement_id: no requirement
    ac_ids: none
    """
    response = admin_client.get('/admin/queue')
    assert response.status_code == 200
    assert b'Verification Queue' in response.data

def test_verify_admin_alerts_page_is_accessible(admin_client):
    """The admin alerts page is accessible to an authenticated admin.

    test_id: cloned_repo__api__020
    target: GET /admin/alerts
    requirement_id: no requirement
    ac_ids: none
    """
    response = admin_client.get('/admin/alerts')
    assert response.status_code == 200
    assert b'Alert Management' in response.data
