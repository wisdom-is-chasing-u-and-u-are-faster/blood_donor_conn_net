import pytest
import io
from app import app, audit_logs


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_social_oauth_login(client):
    """
    AC 1: Users can successfully log in using Google, Apple, or Facebook.
    Tests OAuth 2.0 social login flow for all three required providers (REQ-F-008).
    """
    providers = ["google", "apple", "facebook"]
    for provider in providers:
        # Test web endpoint
        res = client.get(f"/login/social/{provider}", follow_redirects=True)
        assert res.status_code == 200
        assert f"authenticated via {provider.capitalize()}" in res.text or provider in res.text

        # Test REST API endpoint
        api_res = client.post("/api/v1/auth/social", json={"provider": provider})
        assert api_res.status_code == 200
        data = api_res.get_json()
        assert data["status"] == "authenticated"
        assert data["user"]["provider"] == provider
        assert "token" in data


def test_donor_hotspots_clustering(client):
    """
    AC 2: The main dashboard correctly displays a map with donor locations represented as clusters, not precise points.
    Tests Google Maps SDK data simulation and coarse centroid obfuscation (REQ-F-005, REQ-F-006).
    """
    # Test REST API cluster endpoint
    res = client.get("/api/v1/donors/hotspots?radius=25&blood_type=All")
    assert res.status_code == 200
    data = res.get_json()
    assert "clusters" in data
    assert data["total_clusters"] > 0

    first_cluster = data["clusters"][0]
    # Ensure cluster representation has coarse centroids and count
    assert "coarse_latitude" in first_cluster
    assert "coarse_longitude" in first_cluster
    assert "donor_count" in first_cluster
    assert "primary_blood_types" in first_cluster
    assert "street" not in first_cluster  # Exact street address must not be exposed


def test_admin_pending_verifications_list(client):
    """
    AC 3: An administrator can view a list of pending document verifications.
    Tests district administrator queue listing and metadata visibility (REQ-F-009, REQ-F-010).
    """
    res = client.get("/api/v1/admin/verifications")
    assert res.status_code == 200
    data = res.get_json()
    assert "items" in data
    assert data["total_pending"] >= 1
    for item in data["items"]:
        assert item["status"] == "Pending"
        assert "document_type" in item
        assert "user_email" in item


def test_admin_review_approve_and_reject(client):
    """
    AC 4: An administrator can open a specific verification case and click 'Approve' or 'Reject'.
    Tests case inspection and decisioning workflow (REQ-F-009).
    """
    # 1. Test case inspection
    case_res = client.get("/api/v1/admin/verifications/doc-101")
    assert case_res.status_code == 200
    case_data = case_res.get_json()
    assert case_data["id"] == "doc-101"

    # 2. Test Approve action
    approve_res = client.post("/api/v1/admin/verifications/doc-101/action", json={"action": "approve"})
    assert approve_res.status_code == 200
    approve_data = approve_res.get_json()
    assert approve_data["status"] == "Approved"
    assert "verified_by" in approve_data

    # 3. Test Reject action
    reject_res = client.post("/api/v1/admin/verifications/doc-102/action", json={"action": "reject"})
    assert reject_res.status_code == 200
    reject_data = reject_res.get_json()
    assert reject_data["status"] == "Rejected"


def test_document_upload_page_and_endpoint(client):
    """
    AC 5: Users can access a page to upload a file.
    Tests file upload screen access, upload handling, audit trailing, and 30-day retention (REQ-F-003, REQ-F-011).
    """
    # 1. Access upload page
    page_res = client.get("/upload")
    assert page_res.status_code == 200
    assert "Secure Document Upload" in page_res.text or "upload" in page_res.text

    # 2. Upload file via multipart POST
    test_file = (io.BytesIO(b"%PDF-1.4 dummy encrypted medical form content"), "clearance_form.pdf")
    upload_data = {
        "document": test_file,
        "document_type": "Medical Clearance Form",
        "consent": "true",
        "user_email": "tester@bdcn.org"
    }
    upload_res = client.post(
        "/api/v1/documents/upload",
        data=upload_data,
        content_type="multipart/form-data"
    )
    assert upload_res.status_code == 201
    res_data = upload_res.get_json()
    assert res_data["status"] == "Pending"
    assert res_data["retention_days"] == 30
    assert "encrypted_uri" in res_data
    assert "gs://" in res_data["encrypted_uri"]

    # Verify audit log recorded
    assert any("tester@bdcn.org" in log.get("details", "") for log in audit_logs)


def test_service_health_check(client):
    """Tests /health readiness probe endpoint for container orchestration."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "blood_donor_conn_net"


def test_static_ui_pages_serving(client):
    """Tests that all self-contained Variant-A HTML pages are mounted and served cleanly."""
    pages = [
        "/login.html",
        "/dashboard.html",
        "/upload.html",
        "/admin_dashboard.html",
        "/admin_review.html",
        "/index.html"
    ]
    for page in pages:
        res = client.get(page)
        assert res.status_code == 200
        assert len(res.data) > 500
        assert b"api.js" in res.data
