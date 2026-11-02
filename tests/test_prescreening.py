import pytest
import json
from app import app
from blueprints.prescreening import evaluate_rules


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_evaluate_rules_unit():
    """Test clinical pre-screening rule logic directly (REQ-F-002)."""
    # Eligible donor
    status, reasons = evaluate_rules(
        age=25, weight=65.0, last_donation_days=70, chronic_conditions=False, recent_travel=False)
    assert status == "Eligible"
    assert len(reasons) == 0

    # Underage donor (< 18)
    status, reasons = evaluate_rules(
        age=17, weight=65.0, last_donation_days=70)
    assert status == "Deferred"
    assert any("at least 18 years old" in r for r in reasons)

    # Underweight donor (< 50kg)
    status, reasons = evaluate_rules(
        age=22, weight=48.5, last_donation_days=70)
    assert status == "Deferred"
    assert any("at least 50kg" in r for r in reasons)

    # Cool-off interval too short (< 56 days)
    status, reasons = evaluate_rules(
        age=30, weight=70.0, last_donation_days=30)
    assert status == "Deferred"
    assert any("at least 56 days" in r for r in reasons)

    # Chronic conditions or recent travel
    status, reasons = evaluate_rules(
        age=28, weight=75.0, last_donation_days=90, chronic_conditions=True, recent_travel=True)
    assert status == "Deferred"
    assert len(reasons) == 2


def test_prescreening_evaluate_endpoint_eligible(client):
    """Test POST /api/v1/prescreening/evaluate with eligible donor (REQ-F-005, REQ-F-007)."""
    payload = {
        "age": 28,
        "weight": 72.0,
        "last_donation_days": 65,
        "chronic_conditions": False,
        "recent_travel": False,
        "donor_id": "BDC-TEST-001"
    }
    response = client.post(
        "/api/v1/prescreening/evaluate",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "Eligible"
    assert data["reasons"] == []
    assert "prescreening_id" in data
    assert "timestamp" in data


def test_prescreening_evaluate_endpoint_deferred(client):
    """Test POST /api/v1/prescreening/evaluate with multiple deferral reasons (REQ-F-005)."""
    payload = {
        "age": 16,
        "weight": 45.0,
        "last_donation_days": 10,
        "chronic_conditions": True,
        "recent_travel": False
    }
    response = client.post(
        "/api/v1/prescreening/evaluate",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "Deferred"
    assert len(data["reasons"]) >= 3


def test_donor_assessment_page_render(client):
    """Test GET /donor/assessment renders successfully with self-assessment form."""
    response = client.get("/donor/assessment")
    assert response.status_code == 200
    assert b"Donor Eligibility Self-Assessment" in response.data
    assert b"eligibility-form" in response.data
    assert b"last_donation" in response.data
