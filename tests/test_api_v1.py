"""
test_api_v1.py — Validation for ARCH-7789 REST API endpoints and static serving.
"""
import pytest
from app import app, demands, alerts, donors


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test /health probe returns 200 OK and json status."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"


def test_static_page_serving(client):
    """Test static Variant-A HTML pages are accessible under /pages/."""
    res = client.get("/pages/welcome-login.html")
    assert res.status_code == 200
    assert b"Welcome" in res.data or b"BDCN" in res.data


def test_api_social_login_google(client):
    """Test POST /api/v1/auth/social authenticates Google user."""
    payload = {"provider": "google", "token": "mock-token-xyz"}
    res = client.post("/api/v1/auth/social", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["user"]["provider"] == "google"
    assert data["user"]["role"] == "donor"


def test_api_donor_hotspots(client):
    """Test GET /api/v1/donors/hotspots returns privacy-first aggregated data."""
    res = client.get("/api/v1/donors/hotspots?radius=25&blood_type=All")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert isinstance(data["hotspots"], list)
    assert all("distance" in h and h["distance"] <= 25 for h in data["hotspots"])


def test_api_submit_request(client):
    """Test POST /api/v1/requests creates new pending blood demand."""
    payload = {
        "blood_type": "AB+",
        "units": 3,
        "urgency": "Emergency",
        "district": "Downtown",
        "notes": "Trauma ICU patient",
        "filename": "hospital_verification_form.pdf"
    }
    res = client.post("/api/v1/requests", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "success"
    req_id = data["request_id"]
    assert any(d["id"] == req_id and d["blood_type"] == "AB+" for d in demands)


def test_api_verify_request_approve(client):
    """Test POST /api/v1/admin/requests/<id>/verify approves request and emits alert."""
    target_demand = demands[0]
    target_id = target_demand["id"]

    res = client.post(f"/api/v1/admin/requests/{target_id}/verify", json={"action": "approve"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["decision"] == "Approved"
    assert target_demand["status"] == "Approved"
