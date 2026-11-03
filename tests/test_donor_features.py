import pytest
from datetime import date, timedelta
from app import app, donors
from services.eligibility_service import evaluate_eligibility, calculate_age
from services.matching_service import (
    COMPATIBILITY_MATRIX,
    get_compatible_donor_blood_types,
    filter_compatible_verified_donors
)
from services.transaction_service import process_transaction, _IDEMPOTENCY_STORE


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ============================================================================
# 18 INVEST-Grade BDD Gherkin Test Scenarios (REQ-N-004)
# ============================================================================

# Scenario 1: Calculate age correctly
def test_scenario_01_calculate_age():
    """Given a birth date, When calculating age against reference date, Then accurate age is returned."""
    dob = date(2000, 5, 15)
    ref = date(2025, 5, 14)
    assert calculate_age(dob, ref) == 24
    ref2 = date(2025, 5, 15)
    assert calculate_age(dob, ref2) == 25


# Scenario 2: Eligible donor meeting all criteria
def test_scenario_02_prescreening_all_criteria_met():
    """Given an adult donor with valid age, weight >= 50kg, sufficient cool-off, and clean health declaration, When evaluated, Then status is eligible."""
    data = {
        "full_name": "Alice Healthy",
        "dob": "1995-04-12",
        "gender": "female",
        "weight": 58,
        "email": "alice@example.com",
        "last_donation_date": "2024-01-01",
        "health_fever_48h": False,
        "health_malaria_6m": False,
        "declaration_agreed": True
    }
    res = evaluate_eligibility(data, reference_date=date(2025, 1, 1))
    assert res["eligible"] is True
    assert len(res["reasons"]) == 0


# Scenario 3: Underage donor rejected (REQ-F-003: age < 18)
def test_scenario_03_prescreening_underage_rejected():
    """Given a 17-year old applicant, When evaluating pre-screening, Then applicant is rejected with age criterion reason."""
    data = {
        "dob": "2008-01-01",
        "gender": "male",
        "weight": 65,
        "declaration_agreed": True
    }
    res = evaluate_eligibility(data, reference_date=date(2025, 1, 1))
    assert res["eligible"] is False
    assert any("age must be between 18 and 65" in r for r in res["reasons"])


# Scenario 4: Overage donor rejected (REQ-F-003: age > 65)
def test_scenario_04_prescreening_overage_rejected():
    """Given a 66-year old applicant, When evaluating pre-screening, Then applicant is rejected."""
    data = {
        "dob": "1958-01-01",
        "gender": "male",
        "weight": 70,
        "declaration_agreed": True
    }
    res = evaluate_eligibility(data, reference_date=date(2025, 1, 1))
    assert res["eligible"] is False
    assert any("age must be between 18 and 65" in r for r in res["reasons"])


# Scenario 5: Underweight donor rejected (REQ-F-004: weight < 50kg)
def test_scenario_05_prescreening_underweight_rejected():
    """Given a donor weighing 48kg, When evaluated, Then rejected for failing minimum weight requirement."""
    data = {
        "dob": "1998-06-15",
        "gender": "female",
        "weight": 48.5,
        "declaration_agreed": True
    }
    res = evaluate_eligibility(data, reference_date=date(2025, 1, 1))
    assert res["eligible"] is False
    assert any("weight must be at least 50kg" in r for r in res["reasons"])


# Scenario 6: Exact boundary weight (50kg) accepted (REQ-F-004)
def test_scenario_06_prescreening_boundary_weight_accepted():
    """Given a donor weighing exactly 50.0kg, When evaluated, Then weight criterion passes."""
    data = {
        "dob": "1998-06-15",
        "gender": "male",
        "weight": 50.0,
        "declaration_agreed": True
    }
    res = evaluate_eligibility(data, reference_date=date(2025, 1, 1))
    assert not any("weight" in r for r in res["reasons"])


# Scenario 7: Male donation interval < 56 days rejected (REQ-F-005)
def test_scenario_07_prescreening_male_interval_short():
    """Given a male donor who donated 40 days ago (< 56 days), When evaluated, Then interval restriction triggers rejection."""
    ref = date(2025, 5, 1)
    last_donation = ref - timedelta(days=40)
    data = {
        "dob": "1990-01-01",
        "gender": "male",
        "weight": 75,
        "last_donation_date": last_donation.strftime("%Y-%m-%d"),
        "declaration_agreed": True
    }
    res = evaluate_eligibility(data, reference_date=ref)
    assert res["eligible"] is False
    assert any("Minimum donation interval not met" in r and "56 days" in r for r in res["reasons"])


# Scenario 8: Female donation interval < 90 days rejected (REQ-F-005)
def test_scenario_08_prescreening_female_interval_short():
    """Given a female donor who donated 70 days ago (< 90 days), When evaluated, Then interval restriction triggers rejection."""
    ref = date(2025, 5, 1)
    last_donation = ref - timedelta(days=70)
    data = {
        "dob": "1992-01-01",
        "gender": "female",
        "weight": 60,
        "last_donation_date": last_donation.strftime("%Y-%m-%d"),
        "declaration_agreed": True
    }
    res = evaluate_eligibility(data, reference_date=ref)
    assert res["eligible"] is False
    assert any("Minimum donation interval not met" in r and "90 days" in r for r in res["reasons"])


# Scenario 9: Health declaration fever in 48h rejected (REQ-F-006)
def test_scenario_09_prescreening_fever_rejected():
    """Given a donor reporting recent fever, When evaluated, Then applicant is disqualified."""
    data = {
        "dob": "1995-01-01",
        "gender": "male",
        "weight": 70,
        "health_fever_48h": True,
        "declaration_agreed": True
    }
    res = evaluate_eligibility(data, reference_date=date(2025, 1, 1))
    assert res["eligible"] is False
    assert any("fever" in r for r in res["reasons"])


# Scenario 10: Health declaration malaria travel rejected (REQ-F-006)
def test_scenario_10_prescreening_malaria_rejected():
    """Given a donor reporting malaria-risk travel, When evaluated, Then applicant is disqualified."""
    data = {
        "dob": "1995-01-01",
        "gender": "male",
        "weight": 70,
        "health_malaria_6m": True,
        "declaration_agreed": True
    }
    res = evaluate_eligibility(data, reference_date=date(2025, 1, 1))
    assert res["eligible"] is False
    assert any("malaria" in r for r in res["reasons"])


# Scenario 11: Unchecked declaration agreement rejected (REQ-F-006)
def test_scenario_11_prescreening_declaration_disagreed():
    """Given a donor failing to confirm declaration, When evaluated, Then rejected."""
    data = {
        "dob": "1995-01-01",
        "gender": "male",
        "weight": 70,
        "declaration_agreed": False
    }
    res = evaluate_eligibility(data, reference_date=date(2025, 1, 1))
    assert res["eligible"] is False
    assert any("must agree to the health and accuracy declaration" in r for r in res["reasons"])


# Scenario 12: In-memory clinical compatibility matrix matches (REQ-F-007, CONSTRAINT-002)
def test_scenario_12_compatibility_matrix():
    """Given ABO/Rh clinical compatibility rules, When querying compatible donors, Then clinical matches are returned."""
    assert get_compatible_donor_blood_types("O-") == ("O-",)
    assert set(get_compatible_donor_blood_types("O+")) == {"O-", "O+"}
    assert set(get_compatible_donor_blood_types("A+")) == {"O-", "O+", "A-", "A+"}
    assert len(get_compatible_donor_blood_types("AB+")) == 8


# Scenario 13: Urgent request filter only matches verified donors (REQ-F-008, AC 3)
def test_scenario_13_urgent_match_verified_only():
    """Given a pool of verified and unverified donors, When filtering urgent matches, Then unverified donors are strictly excluded."""
    test_donors = [
        {"name": "Verified O-", "blood_group": "O-", "is_verified": True},
        {"name": "Unverified O-", "blood_group": "O-", "is_verified": False},
        {"name": "Verified A+", "blood_group": "A+", "is_verified": True}
    ]
    res = filter_compatible_verified_donors(test_donors, "O-")
    matched_names = [d["name"] for d in res["matched_donors"]]
    assert "Verified O-" in matched_names
    assert "Unverified O-" not in matched_names
    assert "Verified A+" not in matched_names


# Scenario 14: Urgent request filter compatibility for O+ recipient
def test_scenario_14_urgent_match_o_positive_recipient():
    """Given an O+ recipient request, When matching, Then both O- and O+ verified donors are returned."""
    test_donors = [
        {"name": "Donor 1", "blood_group": "O-", "is_verified": True},
        {"name": "Donor 2", "blood_group": "O+", "is_verified": True},
        {"name": "Donor 3", "blood_group": "A+", "is_verified": True}
    ]
    res = filter_compatible_verified_donors(test_donors, "O+")
    matched_names = [d["name"] for d in res["matched_donors"]]
    assert "Donor 1" in matched_names
    assert "Donor 2" in matched_names
    assert "Donor 3" not in matched_names


# Scenario 15: Transaction submission requires Idempotency-Key (REQ-F-009, REQ-F-010)
def test_scenario_15_transaction_missing_idempotency_key(client):
    """Given a transaction request lacking Idempotency-Key, When posted, Then 400 Bad Request is returned."""
    res = client.post("/api/v1/transactions", json={"type": "DISPATCH_MATCH"})
    assert res.status_code == 400
    assert b"Idempotency-Key" in res.data


# Scenario 16: Transaction submission enforces Operator role (REQ-F-011)
def test_scenario_16_transaction_role_enforcement(client):
    """Given an unauthorized role, When submitting transaction, Then 403 Forbidden is returned."""
    res = client.post(
        "/api/v1/transactions",
        headers={"Idempotency-Key": "test-key-123", "X-User-Role": "Guest"},
        json={"type": "DISPATCH_MATCH"}
    )
    assert res.status_code == 403
    assert b"Operator role required" in res.data


# Scenario 17: Transaction idempotency replay (REQ-F-010, REQ-N-005)
def test_scenario_17_transaction_idempotency_replay(client):
    """Given a successful transaction submission, When repeated with identical Idempotency-Key, Then identical transaction is returned with idempotent_replayed=True."""
    key = "idem-key-unique-999"
    payload = {"match_id": "M-101", "units": 2}
    headers = {"Idempotency-Key": key, "X-User-Role": "Operator"}
    
    # First submit
    res1 = client.post("/api/v1/transactions", headers=headers, json=payload)
    assert res1.status_code == 201
    data1 = res1.get_json()
    assert data1["idempotent_replayed"] is False

    # Second submit with same key
    res2 = client.post("/api/v1/transactions", headers=headers, json=payload)
    assert res2.status_code == 201
    data2 = res2.get_json()
    assert data2["idempotent_replayed"] is True
    assert data2["transaction_id"] == data1["transaction_id"]


# Scenario 18: Full UI and API integration for pre-screening evaluation endpoint
def test_scenario_18_api_prescreening_and_ui_views(client):
    """Given UI routes and pre-screening REST endpoint, When accessed, Then correct templates and JSON results are returned."""
    # Test UI routes
    res_dash = client.get("/urgent-dashboard")
    assert res_dash.status_code == 200
    assert b"Urgent Request Dashboard" in res_dash.data

    res_form = client.get("/prescreening-form")
    assert res_form.status_code == 200
    assert b"Pre-Screening" in res_form.data

    # Test POST /api/v1/prescreening/evaluate
    payload = {
        "full_name": "Test Runner",
        "dob": "1990-05-10",
        "gender": "male",
        "weight": 72,
        "declaration_agreed": True
    }
    res_api = client.post("/api/v1/prescreening/evaluate", json=payload)
    assert res_api.status_code == 200
    data = res_api.get_json()
    assert data["eligible"] is True
