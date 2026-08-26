import pytest
from unittest.mock import patch
from app import app
import datetime

"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-12T13:01:24.351373Z
"""

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client

def test_verify_demand_triggers_event_on_approval(client, monkeypatch):
    """Verify `verify_demand` function triggers an event emission on approval.

    test_id: cloned_repo__unit__001
    target: verify_demand
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    mock_demands = [
        {"id": 1, "status": "Approved", "hospital": "Old Hospital", "blood_type": "A+"},
        {"id": 2, "status": "Pending", "hospital": "Test Hospital", "blood_type": "O-"}
    ]
    mock_alerts = []
    mock_audit_logs = []

    monkeypatch.setattr("app.demands", mock_demands)
    monkeypatch.setattr("app.alerts", mock_alerts)
    monkeypatch.setattr("app.audit_logs", mock_audit_logs)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.post("/admin/verify/2", data={"action": "approve"})

    assert response.status_code == 302
    assert len(mock_audit_logs) == 1
    assert mock_audit_logs[0]["action"] == "EMERGENCY DEMAND APPROVED"
    assert "Approved demand #2" in mock_audit_logs[0]["details"]
    assert mock_demands[1]["status"] == "Approved"
    assert len(mock_alerts) == 1
    assert mock_alerts[0]["hospital"] == "Test Hospital"

def test_admin_audit_log_retrieves_log_data(client, monkeypatch):
    """Verify `admin_audit_log` function retrieves log data from the data source.

    test_id: cloned_repo__unit__002
    target: admin_audit_log
    requirement_id: REQ-N-011,REQ-N-012
    ac_ids: REQ-N-011-AC-1,REQ-N-012-AC-1
    """
    mock_logs = [
        {
            "action": "MOCK_ACTION",
            "details": "This is a mock log entry.",
            "user": "mock_user",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    monkeypatch.setattr("app.audit_logs", mock_logs)

    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'test_admin'

    response = client.get("/admin/audit-log")

    assert response.status_code == 200
    assert b"MOCK_ACTION" in response.data
    assert b"This is a mock log entry." in response.data
    assert b"mock_user" in response.data

def test_create_demand_checks_for_authenticated_user(client):
    """Verify `create_demand` function checks for an authenticated user context.

    test_id: cloned_repo__unit__003
    target: create_demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    with patch("app.demands") as mock_demands:
        response = client.post("/hospital/create-demand", data={
            "blood_type": "A+",
            "units": "5",
            "notes": "test notes"
        })

        assert response.status_code == 302
        assert "/login/hospital" in response.location
        mock_demands.append.assert_not_called()