"""Unit tests for Pydantic V2 models and serialization (ARCH-7525)."""

import pytest
from datetime import date
from pydantic import ValidationError

from app.models import DonorEligibilityResponse, TemporalAnomalyError, DonorNotFoundError


def test_donor_eligibility_response_valid():
    """Verify standard valid instantiation of DonorEligibilityResponse."""
    resp = DonorEligibilityResponse(
        donor_id=10482,
        eligible=False,
        last_donation_date=date(2026, 3, 1),
        next_eligible_date=date(2026, 4, 26),
        days_remaining=29,
    )
    assert resp.donor_id == 10482
    assert resp.eligible is False
    assert resp.last_donation_date == date(2026, 3, 1)
    assert resp.next_eligible_date == date(2026, 4, 26)
    assert resp.days_remaining == 29


def test_donor_eligibility_response_first_time_null():
    """Verify first-time donor with null last_donation_date."""
    resp = DonorEligibilityResponse(
        donor_id=12044,
        eligible=True,
        last_donation_date=None,
        next_eligible_date=date(2026, 3, 28),
        days_remaining=0,
    )
    assert resp.eligible is True
    assert resp.last_donation_date is None
    assert resp.days_remaining == 0


def test_donor_eligibility_response_forbids_extra_pii_fields():
    """Verify model strictly forbids extra PII fields (name, email, etc)."""
    with pytest.raises(ValidationError):
        DonorEligibilityResponse(
            donor_id=1001,
            eligible=True,
            last_donation_date=date(2025, 1, 1),
            next_eligible_date=date(2025, 1, 1),
            days_remaining=0,
            name="John Doe",  # Forbidden extra field!
        )


def test_donor_eligibility_response_frozen_immutability():
    """Verify model instance is immutable (frozen=True)."""
    resp = DonorEligibilityResponse(
        donor_id=1001,
        eligible=True,
        last_donation_date=date(2025, 1, 1),
        next_eligible_date=date(2025, 1, 1),
        days_remaining=0,
    )
    with pytest.raises(ValidationError):
        resp.eligible = False


def test_donor_eligibility_response_validation_constraints():
    """Verify field constraints: donor_id >= 1, days_remaining between 0 and 56."""
    with pytest.raises(ValidationError):
        DonorEligibilityResponse(
            donor_id=0,  # Invalid: ge=1 violated
            eligible=True,
            next_eligible_date=date(2026, 3, 28),
            days_remaining=0,
        )

    with pytest.raises(ValidationError):
        DonorEligibilityResponse(
            donor_id=1001,
            eligible=False,
            next_eligible_date=date(2026, 3, 28),
            days_remaining=57,  # Invalid: le=56 violated
        )


def test_rfc7807_error_models():
    """Verify temporal anomaly and not found RFC 7807 error models."""
    anomaly = TemporalAnomalyError(detail="Future date anomaly detected")
    assert anomaly.status == 400
    assert anomaly.code == "TEMPORAL_ANOMALY_FUTURE_DATE"

    not_found = DonorNotFoundError(detail="Donor not found")
    assert not_found.status == 404
    assert not_found.code == "DONOR_NOT_FOUND"
