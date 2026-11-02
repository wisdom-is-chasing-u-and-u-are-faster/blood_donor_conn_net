import pytest
from app import app, verifications, verified_recipients, messages_store

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret"
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test Cloud Run readiness probe."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "healthy"

def test_social_login_google(client):
    """AC: User can log in via Google, Apple, or Facebook."""
    payload = {"provider": "google", "username": "alice_recipient", "role": "recipient"}
    res = client.post("/api/v1/auth/social", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["role"] == "recipient"

def test_social_login_invalid_provider(client):
    """Test validation of social providers."""
    res = client.post("/api/v1/auth/social", json={"provider": "unsupported_oauth"})
    assert res.status_code == 400

def test_recipient_document_upload(client):
    """AC: A recipient can upload a verification document."""
    with client.session_transaction() as sess:
        sess["username"] = "bob_recipient"
        sess["role"] = "recipient"

    payload = {
        "recipient_name": "bob_recipient",
        "hospital_name": "Mercy General",
        "physician_name": "Dr. Sarah Adams",
        "document_type": "Hospital Letter",
        "document_name": "mercy_hospital_letter.pdf"
    }
    res = client.post("/api/v1/verifications/upload", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert "verification_id" in data
    assert data["status"] == "pending"

def test_admin_verification_queue_and_actions(client):
    """AC: An administrator can approve or reject a pending verification."""
    # List verifications
    res = client.get("/api/v1/admin/verifications")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["verifications"]) > 0

    verif_id = data["verifications"][0]["id"]
    # Admin approves
    res_approve = client.post(f"/api/v1/admin/verifications/{verif_id}/action", json={"action": "approve", "notes": "Valid physician signature."})
    assert res_approve.status_code == 200
    assert res_approve.get_json()["status"] == "approved"

    # Reject non-existent returns 404
    res_404 = client.post("/api/v1/admin/verifications/99999/action", json={"action": "reject"})
    assert res_404.status_code == 404

def test_unverified_recipient_map_locked(client):
    """AC: Unverified users cannot view donor hotspots."""
    with client.session_transaction() as sess:
        sess["username"] = "unverified_user"
        sess["role"] = "recipient"

    res = client.get("/api/v1/donors/hotspots")
    assert res.status_code == 403
    assert "Access restricted" in res.get_json()["error"]

def test_verified_recipient_map_unlocked_and_clustered(client):
    """AC: A verified recipient can view a map of donor hotspots. Donor location is never shown precisely on the map, only as part of a cluster."""
    verified_recipients.add("charlie_verified")
    with client.session_transaction() as sess:
        sess["username"] = "charlie_verified"
        sess["role"] = "recipient"

    res = client.get("/api/v1/donors/hotspots")
    assert res.status_code == 200
    data = res.get_json()
    assert data["verified"] is True
    assert len(data["hotspots"]) > 0
    # Coordinates must be coarse centroid clusters without exact residential addresses
    for h in data["hotspots"]:
        assert "cluster_id" in h
        assert "donor_count" in h
        assert isinstance(h["lat"], float)

def test_unverified_contact_locked(client):
    """AC: Unverified users cannot contact donors."""
    with client.session_transaction() as sess:
        sess["username"] = "unverified_stranger"
        sess["role"] = "recipient"

    res = client.post("/api/v1/messages/send", json={"recipient": "john_donor", "content": "Hello!"})
    assert res.status_code == 403
    assert "Contact initiation is locked" in res.get_json()["error"]

def test_verified_messaging_allowed(client):
    """Verified user or donor can send secure message."""
    with client.session_transaction() as sess:
        sess["username"] = "donor_dave"
        sess["role"] = "donor"

    res = client.post("/api/v1/messages/send", json={"recipient": "all", "content": "Available to donate O- blood."})
    assert res.status_code == 201
    assert res.get_json()["success"] is True

def test_social_sharing_badges(client):
    """REQ-F-009: API for social sharing of badges and milestones."""
    res = client.post("/api/v1/achievements/share", json={"badge_id": "top_donor_tier", "platform": "twitter"})
    assert res.status_code == 200
    assert "share_url" in res.get_json()

def test_render_variant_a_pages(client):
    """Verify Variant A UI mockups are served properly."""
    res = client.get("/pages/login.html")
    assert res.status_code == 200
    res_map = client.get("/pages/map.html")
    assert res_map.status_code == 200
