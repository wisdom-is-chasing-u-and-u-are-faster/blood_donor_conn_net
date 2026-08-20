"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-12T13:01:21Z
"""
import pytest
from unittest.mock import patch
from app import app

@pytest.fixture
def client():
    app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
    })
    with app.test_client() as client:
        yield client

def test_cloned_repo__unit__001(client):
    """Verify login function authenticates valid users.

    test_id: cloned_repo__unit__001
    target: login_unified
    requirement_id: no requirement
    ac_ids: none
    """
    mock_donors = [{'username': 'testdonor', 'name': 'Test Donor', 'blood_group': 'A+'}]
    with patch('app.donors', mock_donors), \
         patch('app.audit_logs', []):
        response = client.post('/login', data={
            'username': 'testdonor',
            'password': 'password123', # Note: password is not checked by the target function
            'role': 'donor'
        })

    assert response.status_code == 302
    assert response.location == '/donor/dashboard'

    with client.session_transaction() as sess:
        assert sess.get('role') == 'donor'
        assert sess.get('username') == 'testdonor'

def test_cloned_repo__unit__002_negative_auth(client):
    """Verify login function rejects invalid users.

    test_id: cloned_repo__unit__002_negative_auth
    target: login_unified
    requirement_id: no requirement
    ac_ids: none
    """
    response = client.post('/login', data={
        'username': 'testuser',
        'password': '', # Missing password
        'role': 'donor'
    })

    assert response.status_code == 200
    assert b'Please enter both username and password.' in response.data

    with client.session_transaction() as sess:
        assert 'username' not in sess
        assert 'role' not in sess

def test_cloned_repo__unit__003(client):
    """Verify registration function creates a new user.

    test_id: cloned_repo__unit__003
    target: donor_register
    requirement_id: no requirement
    ac_ids: none
    """
    initial_donors = []
    mock_audit_logs = []
    new_user_data = {
        'name': 'New Donor',
        'username': 'newdonor',
        'age': '30',
        'gender': 'Male',
        'blood_group': 'A+',
        'district': 'Test District'
    }

    with patch('app.donors', initial_donors), \
         patch('app.audit_logs', mock_audit_logs):
        response = client.post('/donor/register', data=new_user_data)

    assert response.status_code == 302
    assert response.location == '/donor/profile'

    assert len(initial_donors) == 1
    created_donor = initial_donors[0]
    assert created_donor['username'] == 'newdonor'
    assert created_donor['name'] == 'New Donor'
    assert created_donor['age'] == 30

    assert len(mock_audit_logs) == 1
    assert mock_audit_logs[0]['action'] == 'DONOR REGISTERED'

    with client.session_transaction() as sess:
        assert sess['role'] == 'donor'
        assert sess['username'] == 'newdonor'

def test_cloned_repo__unit__004(client):
    """Verify admin demand verification function updates status.

    test_id: cloned_repo__unit__004
    target: verify_demand
    requirement_id: no requirement
    ac_ids: none
    """
    with client.session_transaction() as sess:
        sess['username'] = 'testadmin'
        sess['role'] = 'admin'

    mock_demands = [{
        'id': 99,
        'hospital': 'Test Hospital',
        'blood_type': 'B-',
        'units': 2,
        'status': 'Pending',
        'district': 'Test District'
    }]
    mock_alerts = []
    mock_audit_logs = []

    with patch('app.demands', mock_demands), \
         patch('app.alerts', mock_alerts), \
         patch('app.audit_logs', mock_audit_logs), \
         patch('app.match_and_notify_donors') as mock_match_notify:
        
        mock_match_notify.return_value = [{'username': 'donor1'}]
        response = client.post('/admin/verify/99', data={'action': 'approve'})

    assert response.status_code == 302
    assert response.location == '/admin/dashboard'

    assert mock_demands[0]['status'] == 'Approved'
    assert len(mock_alerts) == 1
    assert mock_alerts[0]['demand_id'] == 99
    mock_match_notify.assert_called_once_with(mock_demands[0])
    assert len(mock_audit_logs) == 1
    assert mock_audit_logs[0]['action'] == 'EMERGENCY DEMAND APPROVED'
