import pytest
import io
from unittest.mock import patch
from datetime import datetime

"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   api
Source:  test_strategy/plans/cloned_repo__api.json
Generated: 2024-05-23T01:09:47.022513
"""

from app import app

@pytest.fixture
def client():
    """A test client for the app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_cloned_repo_api_001(client):
    """Verify that an admin can fetch the audit log.

    test_id: cloned_repo__api__001
    target: GET /admin/audit-log
    requirement_id: REQ-N-012
    ac_ids: REQ-N-012-AC-1
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.get('/admin/audit-log')

    assert response.status_code == 200
    # The endpoint renders an HTML template, not JSON.
    assert b'Audit Log' in response.data
    assert b'SYSTEM STARTUP' in response.data

def test_cloned_repo_api_002(client, monkeypatch):
    """Verify a hospital can create a new demand request.

    test_id: cloned_repo__api__002
    target: POST /hospital/create-demand
    requirement_id: REQ-F-015,REQ-N-007
    ac_ids: REQ-F-015-AC-1,REQ-N-007-AC-1
    """
    # Use monkeypatch to control the state of the in-memory database
    initial_demands = []
    monkeypatch.setattr('app.demands', initial_demands)

    with client.session_transaction() as sess:
        sess['role'] = 'hospital'
        sess['username'] = 'test_hospital'

    data = {
        'blood_type': 'B+',
        'units': '5',
        'notes': 'Urgent request',
        'document': (io.BytesIO(b'compliance data'), 'doc.pdf')
    }

    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')

    assert response.status_code == 302
    assert '/hospital/dashboard' in response.location

    assert len(app.demands) == 1
    new_demand = app.demands[0]
    assert new_demand['blood_type'] == 'B+'
    assert new_demand['units'] == 5
    assert new_demand['status'] == 'Pending'
    assert new_demand['hospital'] == 'test_hospital'

def test_cloned_repo_api_002_negative_auth(client):
    """Verify creating a demand fails for unauthenticated users.

    test_id: cloned_repo__api__002_negative_auth
    target: POST /hospital/create-demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    data = {
        'blood_type': 'B+',
        'units': '5',
        'document': (io.BytesIO(b'compliance data'), 'doc.pdf')
    }
    response = client.post('/hospital/create-demand', data=data, content_type='multipart/form-data')

    assert response.status_code == 302
    assert '/login/hospital' in response.location

def test_cloned_repo_api_004(client):
    """Verify home page is accessible.

    test_id: cloned_repo__api__004
    target: GET /
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/')
    # Unauthenticated users are redirected to the login page
    assert response.status_code == 302
    assert '/login/hospital' in response.location

def test_cloned_repo_api_005(client):
    """Verify hospital login page renders.

    test_id: cloned_repo__api__005
    target: GET /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/login/hospital')
    assert response.status_code == 200
    assert b'<form' in response.data
    assert b'Hospital Login' in response.data

def test_cloned_repo_api_006(client):
    """Verify successful hospital login redirects to dashboard.

    test_id: cloned_repo__api__006
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/hospital', data={'username': 'test_hospital', 'password': 'password123'})
    assert response.status_code == 302
    assert '/hospital/dashboard' in response.location

def test_cloned_repo_api_007_negative_creds(client):
    """Verify failed hospital login shows an error.

    test_id: cloned_repo__api__007_negative_creds
    target: POST /login/hospital
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/hospital', data={'username': 'invalid_user', 'password': ''})
    assert response.status_code == 200
    assert b'Invalid credentials.' in response.data

def test_cloned_repo_api_008(client):
    """Verify admin login page renders.

    test_id: cloned_repo__api__008
    target: GET /login/admin
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.get('/login/admin')
    assert response.status_code == 200
    assert b'<form' in response.data
    assert b'Administrator Login' in response.data

def test_cloned_repo_api_009(client):
    """Verify successful admin login redirects to admin page.

    test_id: cloned_repo__api__009
    target: POST /login/admin
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login/admin', data={'username': 'admin_user', 'password': 'admin_password'})
    assert response.status_code == 302
    assert '/admin/queue' in response.location

def test_cloned_repo_api_011(client):
    """Verify logout redirects to home page.

    test_id: cloned_repo__api__011
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

def test_cloned_repo_api_012(client):
    """Verify hospital dashboard is accessible to logged-in hospital user.

    test_id: cloned_repo__api__012
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

def test_cloned_repo_api_014(client):
    """Verify admin queue page is accessible to logged-in admin.

    test_id: cloned_repo__api__014
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

def test_cloned_repo_api_016(client, monkeypatch):
    """Verify an admin can approve a demand request.

    test_id: cloned_repo__api__016
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017,REQ-F-001
    ac_ids: REQ-F-017-AC-1,REQ-F-001-AC-1
    """
    mock_demands = [{
        "id": 123,
        "hospital": "Test Hospital",
        "blood_type": "A+",
        "units": 10,
        "filename": "doc.pdf",
        "status": "Pending"
    }]
    monkeypatch.setattr('app.demands', mock_demands)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.post('/admin/verify/123', data={'action': 'approve'})

    assert response.status_code == 302
    assert '/admin/queue' in response.location
    assert app.demands[0]['status'] == 'Approved'

def test_cloned_repo_api_016_negative_not_found(client):
    """Verify approving a non-existent demand returns an error.

    test_id: cloned_repo__api__016_negative_not_found
    target: POST /admin/verify/<int:demand_id>
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.post('/admin/verify/99999', data={'action': 'approve'}, follow_redirects=True)

    # The app flashes a message and redirects, it does not return 404.
    assert response.status_code == 200
    assert b'Demand request not found.' in response.data
