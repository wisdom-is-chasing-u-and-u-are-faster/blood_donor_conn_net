import pytest
from app import app
from db.init_db import init_database, get_db_connection


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_database(reset=True)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test health and readiness probe (REQ-N-001, REQ-N-002)."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "QuantumLeap" in data["service"]


def test_mockup_pages(client):
    """Test full-fidelity Variant A pages render properly (home, about, services, contact)."""
    for route in ["/home", "/quantum", "/about", "/services", "/contact"]:
        res = client.get(route)
        assert res.status_code == 200, f"Failed on {route}"
        assert b"QuantumLeap" in res.data or b"SynthWave" in res.data


def test_user_registration_ac1(client):
    """AC 1: A new user can successfully register an account (REQ-F-001)."""
    response = client.post("/register", data={
        "full_name": "Sarah Connor",
        "username": "sarah_c",
        "email": "sarah@resistance.org",
        "password": "SecurePassword999!"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert (b"Welcome to QuantumLeap, Sarah Connor" in response.data or
            b"Investment Portfolio Dashboard" in response.data)

    # Verify user exists in database with provisioned accounts
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = 'sarah_c'").fetchone()
    assert user is not None
    assert user["email"] == "sarah@resistance.org"

    accounts = conn.execute("SELECT * FROM accounts WHERE user_id = ?", (user["id"],)).fetchall()
    assert len(accounts) >= 2
    conn.close()


def test_api_user_registration(client):
    """Test REST API registration endpoint."""
    response = client.post("/api/v1/auth/register", json={
        "full_name": "Bruce Wayne",
        "username": "bruce_wayne",
        "email": "bruce@wayne-enterprises.com",
        "password": "BatPassword123!"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "User registered successfully"
    assert data["username"] == "bruce_wayne"


def test_duplicate_registration_rejected(client):
    """Test that duplicate registrations are rejected."""
    client.post("/api/v1/auth/register", json={
        "full_name": "Duplicate User",
        "username": "duplicate_user",
        "email": "dup@example.com",
        "password": "password123"
    })
    # Attempt second registration with same username
    response = client.post("/api/v1/auth/register", json={
        "full_name": "Duplicate User 2",
        "username": "duplicate_user",
        "email": "other@example.com",
        "password": "password123"
    })
    assert response.status_code == 400


def test_user_login_ac2(client):
    """AC 2: An existing user can successfully log in (REQ-F-002)."""
    response = client.post("/login", data={
        "username": "alex_investor",
        "password": "Password123!"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Investment Portfolio Dashboard" in response.data
    assert b"Alex Vance" in response.data or b"alex_investor" in response.data


def test_api_user_login(client):
    """Test REST API authentication endpoint."""
    response = client.post("/api/v1/auth/login", json={
        "username": "alex_investor",
        "password": "Password123!"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Login successful"
    assert data["username"] == "alex_investor"


def test_login_invalid_credentials(client):
    """Test login failure with incorrect credentials."""
    response = client.post("/login", data={
        "username": "alex_investor",
        "password": "WrongPassword!"
    }, follow_redirects=True)
    assert b"Invalid username or password" in response.data


def test_dashboard_summary_ac3(client):
    """AC 3: The dashboard correctly displays a summary of investment accounts (REQ-F-003)."""
    # Sign in first
    client.post("/login", data={
        "username": "alex_investor",
        "password": "Password123!"
    })

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Total Portfolio Net Worth" in response.data
    assert b"Individual Brokerage" in response.data
    assert b"Roth IRA" in response.data
    assert b"High-Yield Cash" in response.data
    assert b"QL-INV-1001" in response.data


def test_api_dashboard_summary(client):
    """Test REST API dashboard summary endpoint (REQ-F-003)."""
    response = client.get("/api/v1/dashboard?user_id=1")
    assert response.status_code == 200
    data = response.get_json()
    assert "accounts" in data
    assert len(data["accounts"]) >= 3
    assert data["total_balance"] > 0


def test_transaction_history_req_f_004(client):
    """REQ-F-004: Users must be able to view detailed transaction history for a single account."""
    client.post("/login", data={
        "username": "alex_investor",
        "password": "Password123!"
    })

    # Account 1 (Brokerage)
    response = client.get("/account/1")
    assert response.status_code == 200
    assert b"Detailed Transaction History" in response.data
    assert b"DEPOSIT" in response.data or b"BUY" in response.data

    # REST API check
    api_res = client.get("/api/v1/accounts/1/transactions")
    assert api_res.status_code == 200
    data = api_res.get_json()
    assert data["account_id"] == 1
    assert len(data["transactions"]) > 0


def test_fund_transfers_ac4(client):
    """AC 4: Fund transfers between a user's own accounts can be completed successfully (REQ-F-005)."""
    # Log in as alex_investor
    client.post("/login", data={
        "username": "alex_investor",
        "password": "Password123!"
    })

    conn = get_db_connection()
    from_before = conn.execute("SELECT balance FROM accounts WHERE id = 3").fetchone()["balance"]
    to_before = conn.execute("SELECT balance FROM accounts WHERE id = 2").fetchone()["balance"]
    conn.close()

    transfer_amount = 500.00

    # Transfer $500 from High-Yield Cash (id 3) to Roth IRA (id 2)
    response = client.post("/transfer", data={
        "from_account_id": 3,
        "to_account_id": 2,
        "amount": transfer_amount,
        "memo": "Monthly Roth IRA savings"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Successfully transferred" in response.data

    # Verify balances updated in database
    conn = get_db_connection()
    from_after = conn.execute("SELECT balance FROM accounts WHERE id = 3").fetchone()["balance"]
    to_after = conn.execute("SELECT balance FROM accounts WHERE id = 2").fetchone()["balance"]
    conn.close()

    assert from_after == pytest.approx(from_before - transfer_amount, 0.01)
    assert to_after == pytest.approx(to_before + transfer_amount, 0.01)


def test_api_fund_transfers(client):
    """Test REST API fund transfer endpoint (REQ-F-005)."""
    response = client.post("/api/v1/transfers", json={
        "user_id": 1,
        "from_account_id": 3,
        "to_account_id": 1,
        "amount": 250.00,
        "memo": "Test API Transfer"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Transfer completed successfully"
    assert data["amount"] == 250.00


def test_transfer_insufficient_funds_rejected(client):
    """Test that transfers exceeding available balance are rejected."""
    client.post("/login", data={
        "username": "alex_investor",
        "password": "Password123!"
    })

    response = client.post("/transfer", data={
        "from_account_id": 3,
        "to_account_id": 2,
        "amount": 99999999.00,
        "memo": "Excessive amount"
    }, follow_redirects=True)

    assert b"Insufficient funds" in response.data


def test_transfer_same_account_rejected(client):
    """Test that transfer to the same account is rejected."""
    client.post("/login", data={
        "username": "alex_investor",
        "password": "Password123!"
    })

    response = client.post("/transfer", data={
        "from_account_id": 1,
        "to_account_id": 1,
        "amount": 100.00
    }, follow_redirects=True)

    assert b"Source and destination accounts must be different" in response.data


def test_support_resources_req_f_009(client):
    """REQ-F-009: Users should be able to access help resources and support channels."""
    response = client.get("/api/v1/support")
    assert response.status_code == 200
    data = response.get_json()
    assert "support_channels" in data
    assert "faq" in data
    assert len(data["support_channels"]) >= 3


def test_contact_submission(client):
    """Test submitting contact message inquiry."""
    response = client.post("/api/v1/contact", json={
        "name": "Bruce Wayne",
        "email": "bruce@wayne-enterprises.com",
        "message": "Inquiry regarding private equity investment options."
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "received"
