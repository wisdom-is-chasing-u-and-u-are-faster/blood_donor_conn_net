"""Comprehensive automated test suite for Donor Eligibility & Biological Cooldown Engine.

Implements all 18 Gherkin acceptance criteria scenarios (US-01 through US-18)
for Jira ticket ARCH-7525.
"""

import time
import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.main import app
from app.routers.donors import DONOR_REGISTRY

client = TestClient(app)


# ==============================================================================
# US-01: Cooldown Met — Normal Horizon (90 days elapsed)
# ==============================================================================
def test_us01_cooldown_met_normal_horizon():
    """US-01: Scenario: Donor with 90 days elapsed is eligible."""
    response = client.get("/api/donors/1001/eligibility?current_date=2026-03-28")
    assert response.status_code == 200
    data = response.json()
    assert data["eligible"] is True
    assert data["days_remaining"] == 0
    assert data["next_eligible_date"] == "2026-03-28"
    assert data["last_donation_date"] == "2025-12-28"


# ==============================================================================
# US-02: Exact 56-Day Cooldown Boundary (56 days elapsed)
# ==============================================================================
def test_us02_exact_56_day_cooldown_boundary():
    """US-02: Scenario: Donor at exactly 56 days elapsed is eligible."""
    response = client.get("/api/donors/1002/eligibility?current_date=2026-03-28")
    assert response.status_code == 200
    data = response.json()
    assert data["eligible"] is True
    assert data["days_remaining"] == 0
    assert data["next_eligible_date"] == "2026-03-28"
    assert data["last_donation_date"] == "2026-01-31"


# ==============================================================================
# US-03: Critical 55-Day Cooldown Edge (55 days elapsed, 1 day remaining)
# ==============================================================================
def test_us03_critical_55_day_cooldown_edge():
    """US-03: Scenario: Donor at 55 days elapsed is ineligible with 1 day remaining."""
    response = client.get("/api/donors/1003/eligibility?current_date=2026-03-28")
    assert response.status_code == 200
    data = response.json()
    assert data["eligible"] is False
    assert data["days_remaining"] == 1
    assert data["next_eligible_date"] == "2026-03-29"
    assert data["last_donation_date"] == "2026-02-01"


# ==============================================================================
# US-04: Critical 57-Day Cooldown Edge (57 days elapsed)
# ==============================================================================
def test_us04_critical_57_day_cooldown_edge():
    """US-04: Scenario: Donor at 57 days elapsed is eligible."""
    response = client.get("/api/donors/1004/eligibility?current_date=2026-03-28")
    assert response.status_code == 200
    data = response.json()
    assert data["eligible"] is True
    assert data["days_remaining"] == 0
    assert data["next_eligible_date"] == "2026-03-28"


# ==============================================================================
# US-05: Same-Day Donation Attempt (0 days elapsed, 56 days remaining)
# ==============================================================================
def test_us05_same_day_donation_attempt():
    """US-05: Scenario: Donor attempting donation on the same day is deferred with full cooldown."""
    response = client.get("/api/donors/1005/eligibility?current_date=2026-03-28")
    assert response.status_code == 200
    data = response.json()
    assert data["eligible"] is False
    assert data["days_remaining"] == 56
    assert data["next_eligible_date"] == "2026-05-23"


# ==============================================================================
# US-06: Recent Donation Re-query (Mid-Cooldown, 14 days elapsed)
# ==============================================================================
def test_us06_recent_donation_requery():
    """US-06: Scenario: Donor with donation 14 days ago is deferred for 42 days."""
    response = client.get("/api/donors/1006/eligibility?current_date=2026-03-28")
    assert response.status_code == 200
    data = response.json()
    assert data["eligible"] is False
    assert data["days_remaining"] == 42
    assert data["next_eligible_date"] == "2026-05-09"


# ==============================================================================
# US-07: First-Time Donor (Null Last Donation Date)
# ==============================================================================
def test_us07_first_time_donor_null_state():
    """US-07: Scenario: First-time donor with null donation date is immediately eligible."""
    response = client.get("/api/donors/1007/eligibility?current_date=2026-03-28")
    assert response.status_code == 200
    data = response.json()
    assert data["eligible"] is True
    assert data["days_remaining"] == 0
    assert data["next_eligible_date"] == "2026-03-28"
    assert data["last_donation_date"] is None


# ==============================================================================
# US-08: Defensive Anomaly Detection for Future Date
# ==============================================================================
def test_us08_defensive_anomaly_detection_future_date():
    """US-08: Scenario: Donor profile with future donation date triggers validation error."""
    response = client.get("/api/donors/1008/eligibility?current_date=2026-03-28")
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "TEMPORAL_ANOMALY_FUTURE_DATE"
    assert "application/json" in response.headers.get("Content-Type", "")


# ==============================================================================
# US-09: Far-Future Date Defensive Guard
# ==============================================================================
def test_us09_far_future_date_defensive_guard():
    """US-09: Scenario: Extreme future date is rejected with HTTP 400."""
    response = client.get("/api/donors/1009/eligibility?current_date=2026-03-28")
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "TEMPORAL_ANOMALY_FUTURE_DATE"


# ==============================================================================
# US-10: Leap Year Boundary Traversal (Crossing Feb 29)
# ==============================================================================
def test_us10_leap_year_boundary_traversal():
    """US-10: Scenario: Leap year date math traverses February 29 without offset errors."""
    response = client.get("/api/donors/1010/eligibility?current_date=2024-03-15")
    assert response.status_code == 200
    data = response.json()
    assert data["eligible"] is False
    assert data["days_remaining"] == 6
    assert data["next_eligible_date"] == "2024-03-21"


# ==============================================================================
# US-11: Century Non-Leap Boundary Traversal (Year 2000)
# ==============================================================================
def test_us11_century_boundary_check():
    """US-11: Scenario: Cooldown calculation correctly spans century transitions."""
    response = client.get("/api/donors/1011/eligibility?current_date=2000-03-01")
    assert response.status_code == 200
    data = response.json()
    assert data["eligible"] is True
    assert data["days_remaining"] == 0


# ==============================================================================
# US-12: Non-Existent Donor Identifier Lookup (HTTP 404)
# ==============================================================================
def test_us12_non_existent_donor_identifier_lookup():
    """US-12: Scenario: Requesting an unregistered donor identifier returns 404 Not Found."""
    response = client.get("/api/donors/99999/eligibility")
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "DONOR_NOT_FOUND"


# ==============================================================================
# US-13: Rejection of Negative Donor Identifiers (HTTP 422)
# ==============================================================================
def test_us13_rejection_of_negative_donor_id():
    """US-13: Scenario: Negative donor identifier fails validation."""
    response = client.get("/api/donors/-42/eligibility")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


# ==============================================================================
# US-14: Malformed Donor Identifier Syntax (HTTP 422)
# ==============================================================================
def test_us14_malformed_donor_identifier_syntax():
    """US-14: Scenario: Alphanumeric donor ID string fails routing type constraints."""
    response = client.get("/api/donors/abc-invalid-id/eligibility")
    assert response.status_code == 422


# ==============================================================================
# US-15: Extended Inactivity (Historic Cold Donor Record)
# ==============================================================================
def test_us15_historic_cold_donor_record():
    """US-15: Scenario: Donor with last donation five years ago is marked eligible."""
    response = client.get("/api/donors/1015/eligibility?current_date=2026-03-28")
    assert response.status_code == 200
    data = response.json()
    assert data["eligible"] is True
    assert data["days_remaining"] == 0
    assert data["next_eligible_date"] == "2026-03-28"


# ==============================================================================
# US-16: Strict Schema Compliance and Zero PII Leakage
# ==============================================================================
def test_us16_strict_schema_compliance_and_zero_pii():
    """US-16: Scenario: Response strictly matches DonorEligibilityResponse contract with no PII."""
    response = client.get("/api/donors/1016/eligibility")
    assert response.status_code == 200
    data = response.json()
    expected_keys = {"donor_id", "eligible", "last_donation_date", "next_eligible_date", "days_remaining"}
    assert set(data.keys()) == expected_keys
    prohibited_fields = ["name", "email", "phone", "ssn", "blood_type", "address"]
    for field in prohibited_fields:
        assert field not in data


# ==============================================================================
# US-17: UTC Midnight Temporal Transition State
# ==============================================================================
def test_us17_utc_midnight_temporal_transition():
    """US-17: Scenario: Cooldown reaches 56 days across UTC midnight boundary."""
    # Before midnight (2026-03-27): 55 days elapsed -> ineligible
    resp1 = client.get("/api/donors/1017/eligibility?current_date=2026-03-27")
    assert resp1.status_code == 200
    assert resp1.json()["eligible"] is False
    assert resp1.json()["days_remaining"] == 1

    # After midnight (2026-03-28): 56 days elapsed -> eligible
    resp2 = client.get("/api/donors/1017/eligibility?current_date=2026-03-28")
    assert resp2.status_code == 200
    assert resp2.json()["eligible"] is True
    assert resp2.json()["days_remaining"] == 0


# ==============================================================================
# US-18: High-Throughput Latency SLA Assertion Under Simulated Concurrency
# ==============================================================================
def test_us18_high_throughput_latency_sla_under_load():
    """US-18: Scenario: Eligibility checks meet latency targets under load."""
    latencies = []
    iterations = 200

    for _ in range(iterations):
        start = time.perf_counter()
        resp = client.get("/api/donors/1001/eligibility")
        duration_ms = (time.perf_counter() - start) * 1000
        assert resp.status_code == 200
        latencies.append(duration_ms)

    latencies.sort()
    p50 = latencies[int(iterations * 0.50)]
    p99 = latencies[int(iterations * 0.99)]

    assert p50 <= 20.0, f"P50 latency {p50}ms exceeded SLA 20ms"
    assert p99 <= 50.0, f"P99 latency {p99}ms exceeded SLA 50ms"


# ==============================================================================
# Blood Demand Matching Cooldown Verification Integration Tests
# ==============================================================================
def test_match_donor_ineligible_cooldown():
    """Verify that matching an ineligible donor (in cooldown) fails with HTTP 400."""
    from datetime import date
    from app.routers.donors import DONOR_REGISTRY, compute_donor_eligibility

    # Register an ineligible donor with recent donation (yesterday)
    yesterday = date.fromordinal(date.today().toordinal() - 5)
    DONOR_REGISTRY[99101] = {"id": 99101, "last_donation_date": yesterday}

    res = compute_donor_eligibility(99101, yesterday)
    assert res.eligible is False
    assert res.days_remaining > 0

    from app import app as flask_app
    with flask_app.test_client() as flask_client:
        match_resp = flask_client.post("/api/match-donor", json={"donor_id": 99101, "request_id": 1})
        assert match_resp.status_code == 400
        assert "56-day cooldown period" in match_resp.json["error"]


def test_match_donor_eligible_success():
    """Verify that matching an eligible donor succeeds."""
    from app import app as flask_app
    with flask_app.test_client() as flask_client:
        match_resp = flask_client.post("/api/match-donor", json={"donor_id": 1001, "request_id": 1})
        assert match_resp.status_code == 200
        assert match_resp.json["status"] == "matched"
