import pytest
from app import app
import io
import datetime

"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   integration
Source:  test_strategy/plans/cloned_repo__integration.json
Generated: 2024-07-12T13:01:21.164258Z
"""

@pytest.fixture
def client():
    """A test client for the app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_cloned_repo_integration_001(client, monkeypatch):
    """Hospital user can create and view a demand request.

    test_id: cloned_repo__integration__001
    target: Hospital User Flow
    requirement_id: REQ-002, REQ-F-004
    """
    # Using monkeypatch to ensure a clean state for the in-memory 'database'
    monkeypatch.setattr('app.demands', [])
    monkeypatch.setattr('app.audit_logs', [])

    # Log in as hospital user and follow redirect to dashboard
    login_res = client.post('/login/hospital', data={
        'username': 'testhospital',
        'password': 'password'
    }, follow_redirects=True)

    assert login_res.status_code == 200
    assert b'Logged in to Hospital Portal successfully!' in login_res.data

    # Create a new demand
    demand_data = {
        'blood_type': 'O+',
        'units': '3',
        'notes': 'Urgent need for surgery',
        'document': (io.BytesIO(b"fake-pdf-content"), 'compliance.pdf')
    }
    create_res = client.post('/hospital/create-demand', data=demand_data,
                             content_type='multipart/form-data',
                             follow_redirects=True)

    assert create_res.status_code == 200
    assert b'Blood demand request submitted successfully' in create_res.data

    # Verify the new demand is on the dashboard
    dashboard_res = client.get('/hospital/dashboard')
    assert dashboard_res.status_code == 200
    assert b'testhospital' in dashboard_res.data
    assert b'O+' in dashboard_res.data
    assert b'3' in dashboard_res.data
    assert b'Pending' in dashboard_res.data
    assert b'compliance.pdf' in dashboard_res.data

    # Verify the underlying data structure was updated
    assert len(app.demands) == 1
    assert app.demands[0]['hospital'] == 'testhospital'
    assert app.demands[0]['status'] == 'Pending'

def test_cloned_repo_integration_002(client, monkeypatch):
    """Admin user can verify a demand request.

    test_id: cloned_repo__integration__002
    target: Admin User Flow
    requirement_id: REQ-003, REQ-F-006, REQ-F-017
    """
    # Setup a pending demand in the mock DB
    initial_demands = [{
        "id": 99,
        "hospital": "General Hospital",
        "blood_type": "B-",
        "units": 2,
        "filename": "doc.pdf",
        "status": "Pending"
    }]
    monkeypatch.setattr('app.demands', initial_demands)
    monkeypatch.setattr('app.audit_logs', [])

    # Log in as admin and get the queue
    login_res = client.post('/login/admin', data={
        'username': 'testadmin',
        'password': 'password'
    }, follow_redirects=True)

    assert login_res.status_code == 200
    # Check that the pending demand is visible
    assert b'B-' in login_res.data
    assert b'Pending' in login_res.data

    # Verify the demand
    verify_res = client.post('/admin/verify/99', data={'action': 'approve'}, follow_redirects=True)

    assert verify_res.status_code == 200
    assert b'Approved demand #99' in verify_res.data

    # Check the queue again, the demand should be gone from the pending list
    assert b'B-' not in verify_res.data

    # Check the underlying data structure was updated
    assert app.demands[0]['id'] == 99
    assert app.demands[0]['status'] == 'Approved'

def test_cloned_repo_integration_003(client, monkeypatch):
    """Verified demand status is reflected on hospital dashboard.

    test_id: cloned_repo__integration__003
    target: Cross-Role Data Consistency
    requirement_id: REQ-002, REQ-003
    """
    # Setup a pending demand from a specific hospital
    initial_demands = [{
        "id": 101,
        "hospital": "myhospital",
        "blood_type": "AB+",
        "units": 1,
        "filename": "doc101.pdf",
        "status": "Pending"
    }]
    monkeypatch.setattr('app.demands', initial_demands)
    monkeypatch.setattr('app.audit_logs', [])

    # 1. As admin, log in and verify the demand.
    client.post('/login/admin', data={'username': 'testadmin', 'password': 'pw'})
    verify_res = client.post('/admin/verify/101', data={'action': 'approve'})
    assert verify_res.status_code == 302 # Redirects to admin queue

    # 2. As hospital user, log in. This overwrites the admin's session cookie.
    hosp_login_res = client.post('/login/hospital', data={
        'username': 'myhospital',
        'password': 'pw'
    }, follow_redirects=True)

    assert hosp_login_res.status_code == 200

    # 3. Verify the status is updated on the hospital's dashboard
    assert b'AB+' in hosp_login_res.data
    assert b'Approved' in hosp_login_res.data
    
    # Verify the underlying data structure to be certain
    demand_after_verify = next((d for d in app.demands if d['id'] == 101), None)
    assert demand_after_verify is not None
    assert demand_after_verify['status'] == 'Approved'
