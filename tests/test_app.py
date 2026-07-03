import pytest
import io
from app import app, demands, alerts


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_home_redirect(client):
    """Test that visiting root redirects to login page when not authenticated."""
    response = client.get("/")
    assert response.status_code == 302
    assert "/login/hospital" in response.headers["Location"]


def test_login_hospital(client):
    """Test login as hospital user."""
    response = client.post("/login/hospital", data={
        "username": "Mercy Hospital",
        "password": "password123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome, Mercy Hospital" in response.data


def test_login_admin(client):
    """Test login as administrator user."""
    response = client.post("/login/admin", data={
        "username": "admin_district",
        "password": "password123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Hospital Request Verification Queue" in response.data


def test_create_demand(client):
    """Test creating a blood demand request."""
    # First login as hospital
    client.post("/login/hospital", data={"username": "Mercy Hospital", "password": "123"})

    # Post blood demand
    data = {
        "blood_type": "B+",
        "units": "8",
        "notes": "Urgent surgery",
        "document": (io.BytesIO(b"dummy compliance contents"), "test_compliance.pdf")
    }
    response = client.post(
        "/hospital/create-demand",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True)
    assert response.status_code == 200
    assert b"Blood demand request submitted successfully" in response.data

    # Assert it exists in mock DB
    latest_demand = demands[-1]
    assert latest_demand["blood_type"] == "B+"
    assert latest_demand["units"] == 8
    assert latest_demand["filename"] == "test_compliance.pdf"


def test_verify_demand_approve(client):
    """Test that admin can approve a pending demand and emit alert."""
    # Add a pending demand
    demand_id = len(demands) + 1
    demands.append({
        "id": demand_id,
        "hospital": "Mercy Hospital",
        "blood_type": "O-",
        "units": 2,
        "filename": "some_doc.pdf",
        "status": "Pending"
    })

    # Login as admin
    client.post("/login/admin", data={"username": "admin_district", "password": "123"})

    # Approve
    response = client.post(f"/admin/verify/{demand_id}", data={"action": "approve"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Approved demand" in response.data

    # Verify status changed
    assert demands[-1]["status"] == "Approved"

    # Verify alert created
    assert alerts[-1]["blood_type"] == "O-"


def test_verify_demand_reject(client):
    """Test that admin can reject a pending demand."""
    demand_id = len(demands) + 1
    demands.append({
        "id": demand_id,
        "hospital": "Mercy Hospital",
        "blood_type": "AB-",
        "units": 1,
        "filename": "some_doc.pdf",
        "status": "Pending"
    })

    # Login as admin
    client.post("/login/admin", data={"username": "admin_district", "password": "123"})

    # Reject
    response = client.post(f"/admin/verify/{demand_id}", data={"action": "reject"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Rejected demand" in response.data

    # Verify status changed
    assert demands[-1]["status"] == "Rejected"
