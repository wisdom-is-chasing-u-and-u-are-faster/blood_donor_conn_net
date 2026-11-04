import pytest
import time
from app import app, donors
from services.eligibility_service import (
    evaluate_donor_eligibility,
    calculate_days_since_donation,
    MIN_DONOR_AGE,
    MAX_DONOR_AGE,
    MIN_DONOR_WEIGHT_KG,
    MIN_DONATION_INTERVAL_DAYS,
)
from services.matching_service import (
    filter_compatible_donors,
    get_compatible_donor_types,
    is_compatible,
    BLOOD_COMPATIBILITY_MATRIX,
)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


# ==============================================================================
# REQ-F-001: Pre-Screening Module Unit Tests
# ==============================================================================

def test_eligibility_fully_eligible():
    """Verify donor meeting all criteria is evaluated as eligible."""
    res = evaluate_donor_eligibility(age=25, weight=65.0, last_donation_date="2025-01-01")
    assert res["is_eligible"] is True
    assert "eligible" in res["message"].lower()
    assert len(res["reasons"]) == 0


def test_eligibility_age_boundaries():
    """Verify age boundaries (18 to 65 inclusive)."""
    # Below minimum age (17)
    res_underage = evaluate_donor_eligibility(age=17, weight=60.0)
    assert res_underage["is_eligible"] is False
    assert any("18" in r for r in res_underage["reasons"])

    # Exactly minimum age (18)
    res_min_age = evaluate_donor_eligibility(age=18, weight=60.0)
    assert res_min_age["is_eligible"] is True

    # Exactly maximum age (65)
    res_max_age = evaluate_donor_eligibility(age=65, weight=60.0)
    assert res_max_age["is_eligible"] is True

    # Above maximum age (66)
    res_overage = evaluate_donor_eligibility(age=66, weight=60.0)
    assert res_overage["is_eligible"] is False
    assert any("65" in r for r in res_overage["reasons"])


def test_eligibility_weight_threshold():
    """Verify minimum weight requirement of 50 kg."""
    # Underweight (49.5 kg)
    res_underweight = evaluate_donor_eligibility(age=30, weight=49.5)
    assert res_underweight["is_eligible"] is False
    assert any("50kg" in r for r in res_underweight["reasons"])

    # Exactly 50.0 kg
    res_exact_weight = evaluate_donor_eligibility(age=30, weight=50.0)
    assert res_exact_weight["is_eligible"] is True


def test_eligibility_donation_interval():
    """Verify cool-off interval of at least 90 days between donations."""
    from datetime import date, timedelta

    # Donated 30 days ago (Ineligible)
    recent_date = (date.today() - timedelta(days=30)).isoformat()
    res_recent = evaluate_donor_eligibility(age=28, weight=55.0, last_donation_date=recent_date)
    assert res_recent["is_eligible"] is False
    assert any("90 days" in r for r in res_recent["reasons"])

    # Donated 120 days ago (Eligible)
    older_date = (date.today() - timedelta(days=120)).isoformat()
    res_older = evaluate_donor_eligibility(age=28, weight=55.0, last_donation_date=older_date)
    assert res_older["is_eligible"] is True

    # First-time donor (No last donation date provided)
    res_first_time = evaluate_donor_eligibility(age=22, weight=58.0, last_donation_date=None)
    assert res_first_time["is_eligible"] is True


# ==============================================================================
# REQ-F-002 & REQ-N-001: Urgent Blood Group Matching Engine Tests
# ==============================================================================

def test_blood_compatibility_matrix_comprehensive():
    """Verify standard RBC ABO/Rh compatibility rules."""
    assert get_compatible_donor_types("O-") == ("O-",)
    assert set(get_compatible_donor_types("O+")) == {"O-", "O+"}
    assert set(get_compatible_donor_types("A-")) == {"O-", "A-"}
    assert set(get_compatible_donor_types("A+")) == {"O-", "O+", "A-", "A+"}
    assert set(get_compatible_donor_types("B-")) == {"O-", "B-"}
    assert set(get_compatible_donor_types("B+")) == {"O-", "O+", "B-", "B+"}
    assert set(get_compatible_donor_types("AB-")) == {"O-", "A-", "B-", "AB-"}
    assert len(get_compatible_donor_types("AB+")) == 8  # Universal recipient


def test_filter_compatible_donors_logic():
    """Test filtering donor collection for given recipient blood type."""
    test_donors = [
        {"name": "Alice", "blood_group": "O-", "phone": "1234567890"},
        {"name": "Bob", "blood_group": "A+", "phone": "9876543210"},
        {"name": "Charlie", "blood_group": "B+", "phone": "5555555555"},
        {"name": "Diana", "blood_group": "AB+", "phone": "4444444444"},
    ]

    # Recipient needs A- -> Compatible with O-, A-
    matched_a_neg = filter_compatible_donors(test_donors, "A-")
    matched_names = [d["name"] for d in matched_a_neg]
    assert "Alice" in matched_names
    assert "Bob" not in matched_names
    assert "Charlie" not in matched_names

    # Verify PII contact masking
    assert matched_a_neg[0]["contact_information"].startswith("+1-XXX-XXX-")


def test_matching_latency_sla_under_500ms(client):
    """REQ-N-001: Urgent blood group matching filter must return within < 500 ms."""
    start = time.perf_counter()
    response = client.get("/api/v1/dashboard/donors/filter?blood_group=A+")
    duration_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    assert duration_ms < 500.0, f"Matching query took {duration_ms}ms, exceeded 500ms SLA"
    data = response.get_json()
    assert data["requested_blood_group"] == "A+"
    assert "compatible_blood_groups" in data
    assert isinstance(data["donors"], list)


# ==============================================================================
# UI Views & Full-Stack Acceptance Criteria Integration Tests
# ==============================================================================

def test_prescreening_ui_accessible(client):
    """AC 1 & 2: A user can access pre-screening form capturing age, weight, last donation."""
    response = client.get("/prescreening")
    assert response.status_code == 200
    assert b"Donor Eligibility Pre-Screening" in response.data
    assert b'id="donorAge"' in response.data
    assert b'id="donorWeight"' in response.data
    assert b'id="lastDonationDate"' in response.data


def test_prescreening_api_evaluate(client):
    """Test POST /api/v1/prescreening/evaluate endpoint."""
    # Test valid eligible payload
    resp_ok = client.post("/api/v1/prescreening/evaluate", json={
        "age": 28,
        "weight": 62.5,
        "last_donation_date": "2024-01-01"
    })
    assert resp_ok.status_code == 200
    data_ok = resp_ok.get_json()
    assert data_ok["is_eligible"] is True

    # Test invalid ineligible payload
    resp_no = client.post("/api/v1/prescreening/evaluate", json={
        "age": 16,
        "weight": 45.0
    })
    assert resp_no.status_code == 200
    data_no = resp_no.get_json()
    assert data_no["is_eligible"] is False


def test_dashboard_urgent_matching_filter_integrated(client):
    """AC 3 & 4: User accesses dashboard with urgent blood group filter returning compatible donors."""
    # Authenticate as hospital
    client.post("/login/hospital", data={
        "username": "General Hospital",
        "password": "password123"
    })

    # Access dashboard with blood group query
    response = client.get("/hospital/dashboard?blood_group=O-")
    assert response.status_code == 200
    assert b"Urgent Blood Group Matching" in response.data
    assert b'id="bloodGroupFilter"' in response.data
    assert b'id="compatibleDonorsTbody"' in response.data
    # O- donor (Jane Smith) should be present
    assert b"Jane Smith" in response.data


def test_health_check_endpoint(client):
    """Verify health probe for container orchestration readiness."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
