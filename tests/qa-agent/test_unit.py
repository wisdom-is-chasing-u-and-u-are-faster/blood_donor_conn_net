"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-18T12:06:48.059438Z
"""
import pytest
from unittest.mock import patch, MagicMock
import io

from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client

def test_cloned_repo_unit_001_home(client):
    """Verifies that the home() function redirects to the login page for an unauthenticated user.

    test_id: cloned_repo__unit__001
    target: home
    requirement_id: no requirement
    """
    response = client.get("/")
    assert response.status_code == 302
    assert response.location == "/login/hospital"

def test_cloned_repo_unit_002_login_hospital(client):
    """Verifies that login_hospital() authenticates a user and sets the session.

    test_id: cloned_repo__unit__002
    target: login_hospital
    requirement_id: REQ-001
    """
    with client.session_transaction() as sess:
        sess.clear()

    with patch('app.audit_logs', []) as mock_audit_logs:
        response = client.post("/login/hospital", data={
            "username": "test_hospital",
            "password": "password123"
        }, follow_redirects=False)

    assert response.status_code == 302
    assert response.location == "/hospital/dashboard"

    with client.session_transaction() as sess:
        assert sess.get("username") == "test_hospital"
        assert sess.get("role") == "hospital"

def test_cloned_repo_unit_003_login_admin(client):
    """Verifies that login_admin() rejects invalid credentials and shows an error.

    test_id: cloned_repo__unit__003
    target: login_admin
    requirement_id: REQ-001
    """
    response = client.post("/login/admin", data={
        "username": "admin",
        "password": ""
    })

    assert response.status_code == 200
    assert b"Invalid credentials." in response.data

def test_cloned_repo_unit_004_logout(client):
    """Verifies that the logout() function clears the session and redirects.

    test_id: cloned_repo__unit__004
    target: logout
    requirement_id: no requirement
    """
    with client.session_transaction() as sess:
        sess["username"] = "test_user"
        sess["role"] = "hospital"

    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 302
    assert response.location == "/login/hospital"

    with client.session_transaction() as sess:
        assert "username" not in sess
        assert "role" not in sess

def test_cloned_repo_unit_005_create_demand(client):
    """Verifies that create_demand() saves valid data when a hospital user is logged in.

    test_id: cloned_repo__unit__005
    target: create_demand
    requirement_id: REQ-002,REQ-F-004,REQ-F-005
    """
    with client.session_transaction() as sess:
        sess["username"] = "test_hospital"
        sess["role"] = "hospital"

    mock_demands = []
    mock_audit_logs = []
    file_data = (io.BytesIO(b"compliance data"), "compliance.pdf")

    with patch('app.demands', mock_demands), patch('app.audit_logs', mock_audit_logs):
        response = client.post("/hospital/create-demand", data={
            "blood_type": "A+",
            "units": "5",
            "document": file_data,
            "notes": "Urgent need"
        }, content_type='multipart/form-data', follow_redirects=False)

    assert response.status_code == 302
    assert response.location == "/hospital/dashboard"
    assert len(mock_demands) == 1
    created_demand = mock_demands[0]
    assert created_demand["hospital"] == "test_hospital"
    assert created_demand["blood_type"] == "A+"
    assert created_demand["units"] == 5
    assert created_demand["filename"] == "compliance.pdf"
    assert created_demand["status"] == "Pending"
    assert len(mock_audit_logs) == 1

def test_cloned_repo_unit_006_verify_demand(client):
    """Verifies that verify_demand() correctly updates a demand's status.

    test_id: cloned_repo__unit__006
    target: verify_demand
    requirement_id: REQ-003,REQ-F-006
    """
    with client.session_transaction() as sess:
        sess["username"] = "test_admin"
        sess["role"] = "admin"

    mock_demands = [{
        "id": 1,
        "hospital": "General Hospital",
        "blood_type": "O-",
        "units": 4,
        "filename": "doc.pdf",
        "status": "Pending"
    }]
    mock_alerts = []

    with patch('app.demands', mock_demands), patch('app.alerts', mock_alerts):
        response = client.post("/admin/verify/1", data={"action": "approve"}, follow_redirects=False)

    assert response.status_code == 302
    assert response.location == "/admin/queue"
    assert mock_demands[0]["status"] == "Approved"
    assert len(mock_alerts) == 1
    assert mock_alerts[0]["hospital"] == "General Hospital"
