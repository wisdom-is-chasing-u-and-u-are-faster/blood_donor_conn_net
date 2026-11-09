"""Donors router module for biological cooldown & eligibility verification.

Implements GET /api/donors/{donor_id}/eligibility per ARCH-7525.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Dict, Optional, Union
from fastapi import APIRouter, Path, Query, status
from fastapi.responses import JSONResponse

from app.models import (
    DonorEligibilityResponse,
    DonorNotFoundError,
    TemporalAnomalyError,
    MatchDonorRequest,
)

router = APIRouter(prefix="/api/donors", tags=["donors"])

# Master in-memory registry of donors for lookups
# Seeded with diverse records for testing and operations
DONOR_REGISTRY: Dict[int, Dict[str, Optional[Union[int, str, date]]]] = {
    1001: {"id": 1001, "last_donation_date": date(2025, 12, 28)},
    1002: {"id": 1002, "last_donation_date": date(2026, 1, 31)},
    1003: {"id": 1003, "last_donation_date": date(2026, 2, 1)},
    1004: {"id": 1004, "last_donation_date": date(2026, 1, 30)},
    1005: {"id": 1005, "last_donation_date": date(2026, 3, 28)},
    1006: {"id": 1006, "last_donation_date": date(2026, 3, 14)},
    1007: {"id": 1007, "last_donation_date": None},  # first-time donor
    1008: {"id": 1008, "last_donation_date": date(2026, 3, 29)},  # future date relative to 2026-03-28
    1009: {"id": 1009, "last_donation_date": date(2099, 12, 31)},  # far-future date
    1010: {"id": 1010, "last_donation_date": date(2024, 1, 25)},
    1011: {"id": 1011, "last_donation_date": date(2000, 1, 5)},
    1015: {"id": 1015, "last_donation_date": date(2021, 3, 28)},
    1016: {
        "id": 1016,
        "last_donation_date": date(2025, 12, 1),
        "name": "Classified Name",
        "email": "classified@domain.org",
        "phone": "+15551234567",
        "ssn": "000-00-0000",
        "blood_type": "O-",
        "address": "123 Classified St",
    },
    1017: {"id": 1017, "last_donation_date": date(2026, 1, 31)},
    4501: {"id": 4501, "last_donation_date": date(2026, 1, 15)},
    8920: {"id": 8920, "last_donation_date": date(2026, 3, 10)},
    10482: {"id": 10482, "last_donation_date": date(2026, 3, 1)},
    12044: {"id": 12044, "last_donation_date": None},
    9999: {"id": 9999, "last_donation_date": date(2026, 4, 15)},  # future
}


def compute_donor_eligibility(
    donor_id: int,
    last_donation_date: Optional[date],
    reference_date: Optional[date] = None,
) -> Union[DonorEligibilityResponse, JSONResponse]:
    """In-memory biological cooldown engine evaluating 56-day whole-blood rule.

    - Condition A: donor_id does not exist -> handled upstream by caller
    - Condition B: last_donation_date IS NULL -> eligible=True, days_remaining=0, next_eligible_date=today_utc
    - Condition C: last_donation_date > today_utc -> HTTP 400 TEMPORAL_ANOMALY_FUTURE_DATE
    - Condition D: (today_utc - last_donation_date).days < 56 -> eligible=False, days_remaining=56-delta, next_eligible_date=last+56d
    - Condition E: (today_utc - last_donation_date).days >= 56 -> eligible=True, days_remaining=0, next_eligible_date=today_utc
    """
    today_utc = reference_date or datetime.now(timezone.utc).date()

    # Null historical donation date handling (First-time donors)
    if last_donation_date is None:
        return DonorEligibilityResponse(
            donor_id=donor_id,
            eligible=True,
            last_donation_date=None,
            next_eligible_date=today_utc,
            days_remaining=0,
        )

    # Defensive Temporal Anomaly Detection: future donation date check
    if last_donation_date > today_utc:
        err = TemporalAnomalyError(
            detail=(
                f"Donor last_donation_date {last_donation_date.isoformat()} exists in "
                f"the future relative to UTC clock {today_utc.isoformat()}."
            ),
            instance=f"/api/donors/{donor_id}/eligibility",
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=err.model_dump(exclude_none=True),
            media_type="application/json",
        )

    # Calculate biological interval delta
    delta_days = (today_utc - last_donation_date).days

    if delta_days >= 56:
        return DonorEligibilityResponse(
            donor_id=donor_id,
            eligible=True,
            last_donation_date=last_donation_date,
            next_eligible_date=today_utc,
            days_remaining=0,
        )
    else:
        days_remaining = 56 - delta_days
        next_eligible_date = last_donation_date + timedelta(days=56)
        return DonorEligibilityResponse(
            donor_id=donor_id,
            eligible=False,
            last_donation_date=last_donation_date,
            next_eligible_date=next_eligible_date,
            days_remaining=days_remaining,
        )


@router.get(
    "/{donor_id}/eligibility",
    response_model=DonorEligibilityResponse,
    responses={
        200: {"model": DonorEligibilityResponse, "description": "Eligibility evaluation result"},
        400: {"model": TemporalAnomalyError, "description": "Future donation date detected"},
        404: {"model": DonorNotFoundError, "description": "Donor not found in master registry"},
        422: {"description": "Path parameter validation failure"},
    },
    summary="Verify Donor Cooldown Eligibility",
)
def get_donor_eligibility(
    donor_id: int = Path(..., ge=1, description="Master identification number of the donor entity"),
    current_date: Optional[date] = Query(None, description="Optional override reference UTC date for testing"),
):
    """Verifies a 56-calendar-day (8-week) biological regeneration period between

    whole blood donations before allowing them to be matched to a new blood request.
    """
    donor = DONOR_REGISTRY.get(donor_id)
    if not donor:
        err = DonorNotFoundError(
            detail=f"Donor with identifier {donor_id} does not exist in the master registry.",
            instance=f"/api/donors/{donor_id}/eligibility",
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=err.model_dump(exclude_none=True),
            media_type="application/json",
        )

    last_date = donor.get("last_donation_date")
    result = compute_donor_eligibility(
        donor_id=donor_id,
        last_donation_date=last_date,
        reference_date=current_date,
    )
    return result
