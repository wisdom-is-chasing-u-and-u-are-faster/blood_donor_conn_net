"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   integration
Source:  test_strategy/plans/cloned_repo__integration.json
Generated: 2024-05-21T16:30:00Z
"""
import pytest
from app import app
import io

@pytest.fixture
def client():
    """Create a Flask test client for the application."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key-for-sessions'
    with app.test_client() as client:
        yield client

def test_hospital_user_login_and_session_management(client):
    """Verifies a hospital user can log in and access a protected dashboard.

    test_id: cloned_repo__integration__001
    target: POST /login/hospital
    requirement_id: REQ-001
    """
    # Log in with valid credentials
    login_response = client.post('/login/hospital', data={
        'username': 'test_hospital',
        'password': 'password123'
    }, follow_redirects=False)

    assert login_response.status_code == 302, "Login should redirect on success"
    assert '/hospital/dashboard' in login_response.location, "Should redirect to the hospital dashboard"

    # The test client handles session cookies, so the next request is authenticated
    dashboard_response = client.get('/hospital/dashboard')
    assert dashboard_response.status_code == 200, "Dashboard should be accessible after login"
    assert b'Hospital Dashboard' in dashboard_response.data or b'Current Demands' in dashboard_response.data, "Dashboard content not found"

def test_role_based_access_control_between_hospital_and_admin(client):
    """Verifies a hospital user cannot access admin-only pages.

    test_id: cloned_repo__integration__002
    target: GET /admin/queue
    requirement_id: REQ-001
    """
    # Log in as a hospital user first
    client.post('/login/hospital', data={
        'username': 'test_hospital',
        'password': 'password123'
    })

    # Attempt to access an admin-only route
    admin_page_response = client.get('/admin/queue', follow_redirects=False)

    # Expect a redirect to the admin login page as per source code logic
    assert admin_page_response.status_code == 302, "Should redirect unauthorized users"
    assert '/login/admin' in admin_page_response.location, "Should redirect to the admin login page"

def test_full_demand_creation_and_verification_lifecycle(client, monkeypatch):
    """Verifies the end-to-end flow of creating and approving a demand.

    test_id: cloned_repo__integration__003
    target: Workflow
    requirement_id: REQ-002,REQ-003,REQ-F-017
    """
    # Use a clean copy of the demands list to avoid test interference
    initial_demands = [d.copy() for d in app.demands]
    monkeypatch.setattr('app.demands', initial_demands)

    # 1. Log in as hospital user
    client.post('/login/hospital', data={'username': 'test_hospital', 'password': 'pw'})

    # 2. Create a new demand
    demand_data = {
        'blood_type': 'B+',
        'units': '3',
        'document': (io.BytesIO(b'mock compliance doc'), 'compliance.pdf')
    }
    create_response = client.post('/hospital/create-demand', data=demand_data, content_type='multipart/form-data')
    assert create_response.status_code == 302
    assert '/hospital/dashboard' in create_response.location

    # 3. Confirm demand was created with 'Pending' status
    assert len(app.demands) == len(initial_demands) + 1, "A new demand should be added"
    new_demand = app.demands[-1]
    assert new_demand['status'] == 'Pending'
    assert new_demand['hospital'] == 'test_hospital'
    demand_id_to_verify = new_demand['id']

    # 4. Log out
    client.get('/logout')

    # 5. Log in as admin user
    client.post('/login/admin', data={'username': 'test_admin', 'password': 'pw'})

    # 6. Approve the demand
    verify_response = client.post(f'/admin/verify/{demand_id_to_verify}', data={'action': 'approve'})
    assert verify_response.status_code == 302
    assert '/admin/queue' in verify_response.location

    # 7. Confirm the demand's status is now 'Approved'
    verified_demand = next((d for d in app.demands if d['id'] == demand_id_to_verify), None)
    assert verified_demand is not None, "The verified demand should still exist"
    assert verified_demand['status'] == 'Approved', "Demand status should be updated to 'Approved'"

def test_unauthenticated_access_to_protected_routes(client):
    """Verifies unauthenticated users are redirected from protected routes.

    test_id: cloned_repo__integration__004
    target: GET /hospital/dashboard
    requirement_id: REQ-N-007
    """
    # With a fresh client (no login), attempt to access a protected route
    response = client.get('/hospital/dashboard', follow_redirects=False)

    assert response.status_code == 302, "Accessing a protected route without auth should redirect"
    assert '/login/hospital' in response.location, "Should redirect to the hospital login page"
