"""Models module for Blood Donor Connection Network.

Defines Pydantic V2 data validation schemas and ORM representations
for donor eligibility and biological cooldown checking per ARCH-7525.
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DonorEligibilityResponse(BaseModel):
    """Pydantic V2 response contract delivering calculated biological

    eligibility status and cooldown metrics for a specific donor.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "donor_id": 10482,
                "eligible": False,
                "last_donation_date": "2026-03-01",
                "next_eligible_date": "2026-04-26",
                "days_remaining": 29,
            }
        },
    )

    donor_id: int = Field(
        ...,
        description="Unique system identifier of the donor.",
        ge=1,
        examples=[10482],
    )
    eligible: bool = Field(
        ...,
        description=(
            "True if donor has satisfied the 56-day whole blood cooldown "
            "or has never donated."
        ),
    )
    last_donation_date: Optional[date] = Field(
        default=None,
        description=(
            "ISO 8601 calendar date of the last whole blood donation. "
            "Null for first-time donors."
        ),
    )
    next_eligible_date: date = Field(
        ...,
        description=(
            "Earliest calendar date when the donor may next donate. "
            "Equals today if eligible."
        ),
    )
    days_remaining: int = Field(
        ...,
        description=(
            "Remaining calendar days in cooldown period. "
            "Zero if currently eligible."
        ),
        ge=0,
        le=56,
    )


class TemporalAnomalyError(BaseModel):
    """RFC 7807 problem details error model for future-dated donation anomalies."""

    type: str = Field(
        default="https://api.blooddonorconn.net/errors/temporal-anomaly"
    )
    title: str = Field(default="Invalid Historical Temporal Reference")
    status: int = Field(default=400)
    detail: str
    code: str = Field(default="TEMPORAL_ANOMALY_FUTURE_DATE")
    instance: Optional[str] = None


class DonorNotFoundError(BaseModel):
    """RFC 7807 problem details error model for missing donor lookups."""

    type: str = Field(default="https://api.blooddonorconn.net/errors/not-found")
    title: str = Field(default="Donor Profile Not Found")
    status: int = Field(default=404)
    detail: str
    code: str = Field(default="DONOR_NOT_FOUND")
    instance: Optional[str] = None


class MatchDonorRequest(BaseModel):
    """Request payload for matching a donor to a blood demand."""

    donor_id: int = Field(..., ge=1)
    request_id: int = Field(..., ge=1)
