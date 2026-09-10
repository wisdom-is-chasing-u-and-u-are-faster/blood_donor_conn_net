"""
Test Suite for Automated Rolling Donor Eligibility Engine (ARCH-1184, ARCH-1185, ARCH-1186)
Validates 56-day whole blood rule, 112-day double red cell rule, 7-day platelet rule,
medical deferrals, leap years, boundary timestamp checks, and AC scenarios.
"""
import pytest
from datetime import datetime
from services.eligibility_service import fn_validate_donor_eligibility, INTERVAL_DAYS


@pytest.fixture
def marcus_vance_donor():
    return {
        "donor_id": "d0000000-0000-0000-0000-000000000001",
        "first_name": "Marcus",
        "last_name": "Vance",
        "abo_type": "O",
        "rh_factor": "NEGATIVE",
        "is_active": True,
        "is_deferred": False,
        "deferral_reason": None,
        "deferral_end_date": None
    }


def test_first_time_donor_clearance():
    donor = {"donor_id": "new-donor-1", "is_active": True, "is_deferred": False}
    result = fn_validate_donor_eligibility(donor, [], donation_type="WHOLE_BLOOD", target_date="2025-01-01")
    assert result["isEligible"] is True
    assert result["daysRemaining"] == 0
    assert result["blockReason"] == "ELIGIBLE_FIRST_TIME"


def test_scenario_1_whole_blood_day_55_block(marcus_vance_donor):
    """
    Jira Scenario 1:
    Given donor Marcus Vance donated WHOLE_BLOOD on 2024-12-25,
    When Marcus attempts to book or be matched on 2025-02-18 (Day 55),
    Then the eligibility service returns isEligible: false,
    blockReason: MINIMUM_DONATION_INTERVAL_NOT_MET, nextEligibleDate: 2025-02-19T00:00:00Z.
    """
    history = [{
        "donation_type": "WHOLE_BLOOD",
        "collected_at": "2024-12-25T10:00:00Z"
    }]
    target_date = "2025-02-18"  # 55 days later
    res = fn_validate_donor_eligibility(marcus_vance_donor, history, "WHOLE_BLOOD", target_date)
    assert res["isEligible"] is False
    assert res["daysRemaining"] == 1
    assert res["blockReason"] == "MINIMUM_DONATION_INTERVAL_NOT_MET"
    assert "2025-02-19" in res["nextEligibleDate"]


def test_scenario_2_whole_blood_day_56_clearance(marcus_vance_donor):
    """
    Jira Scenario 2:
    Given donor Marcus Vance donated WHOLE_BLOOD on 2024-12-25,
    When Marcus checks eligibility on 2025-02-19 (Day 56),
    Then the eligibility service returns isEligible: true with daysRemaining: 0.
    """
    history = [{
        "donation_type": "WHOLE_BLOOD",
        "collected_at": "2024-12-25T10:00:00Z"
    }]
    target_date = "2025-02-19"  # Day 56
    res = fn_validate_donor_eligibility(marcus_vance_donor, history, "WHOLE_BLOOD", target_date)
    assert res["isEligible"] is True
    assert res["daysRemaining"] == 0
    assert res["blockReason"] == "ELIGIBLE"


def test_double_red_cells_112_day_interval(marcus_vance_donor):
    history = [{
        "donation_type": "DOUBLE_RED_CELLS",
        "collected_at": "2025-01-01T00:00:00Z"
    }]
    # Day 111: Blocked
    res_111 = fn_validate_donor_eligibility(marcus_vance_donor, history, "DOUBLE_RED_CELLS", "2025-04-22")
    assert res_111["isEligible"] is False
    assert res_111["daysRemaining"] == 1
    assert res_111["blockReason"] == "MINIMUM_DONATION_INTERVAL_NOT_MET"

    # Day 112: Cleared
    res_112 = fn_validate_donor_eligibility(marcus_vance_donor, history, "DOUBLE_RED_CELLS", "2025-04-23")
    assert res_112["isEligible"] is True
    assert res_112["daysRemaining"] == 0


def test_platelet_7_day_interval(marcus_vance_donor):
    history = [{
        "donation_type": "PLATELETS",
        "collected_at": "2025-05-01T10:00:00Z"
    }]
    # Day 6: Blocked
    res_6 = fn_validate_donor_eligibility(marcus_vance_donor, history, "PLATELETS", "2025-05-07")
    assert res_6["isEligible"] is False
    assert res_6["daysRemaining"] == 1

    # Day 7: Cleared
    res_7 = fn_validate_donor_eligibility(marcus_vance_donor, history, "PLATELETS", "2025-05-08")
    assert res_7["isEligible"] is True
    assert res_7["daysRemaining"] == 0


def test_active_medical_deferral_override(marcus_vance_donor):
    marcus_vance_donor["is_deferred"] = True
    marcus_vance_donor["deferral_reason"] = "LOW_HEMOGLOBIN"
    marcus_vance_donor["deferral_end_date"] = "2025-06-01"

    # Even if 100 days have passed since donation, deferral blocks
    history = [{"donation_type": "WHOLE_BLOOD", "collected_at": "2024-01-01T00:00:00Z"}]
    res = fn_validate_donor_eligibility(marcus_vance_donor, history, "WHOLE_BLOOD", "2025-05-15")
    assert res["isEligible"] is False
    assert res["blockReason"] == "LOW_HEMOGLOBIN"
    assert res["daysRemaining"] == 17

    # After deferral end date has passed, eligibility returns true
    res_after = fn_validate_donor_eligibility(marcus_vance_donor, history, "WHOLE_BLOOD", "2025-06-02")
    assert res_after["isEligible"] is True


def test_leap_year_boundary_calculation(marcus_vance_donor):
    # 2024 was a leap year (Feb 29 exists)
    history = [{"donation_type": "WHOLE_BLOOD", "collected_at": "2024-01-15T00:00:00Z"}]
    # 56 days from Jan 15 2024 -> Jan has 31-15=16 days, Feb has 29 days (45), March 11 is Day 56
    res_day55 = fn_validate_donor_eligibility(marcus_vance_donor, history, "WHOLE_BLOOD", "2024-03-10")
    assert res_day55["isEligible"] is False
    assert res_day55["daysRemaining"] == 1

    res_day56 = fn_validate_donor_eligibility(marcus_vance_donor, history, "WHOLE_BLOOD", "2024-03-11")
    assert res_day56["isEligible"] is True
