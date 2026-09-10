"""
Eligibility Service - Automated Rolling Donor Eligibility Engine
Enforces 56-day whole blood, 112-day double red cell, and 7-day platelet rules,
as well as medical deferrals and boundary calculations under FDA 21 CFR Part 606.
"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List

# Minimum donation interval constants in calendar days
INTERVAL_DAYS = {
    "WHOLE_BLOOD": 56,
    "DOUBLE_RED_CELLS": 112,
    "PLATELETS": 7,
    "PLASMA": 28,
}

# Maximum allowed platelet donations per 365 rolling days
MAX_PLATELET_ANNUAL_LIMIT = 24


def parse_datetime(dt_val: Any) -> Optional[datetime]:
    if dt_val is None:
        return None
    if isinstance(dt_val, datetime):
        return dt_val
    if isinstance(dt_val, date):
        return datetime.combine(dt_val, datetime.min.time())
    if isinstance(dt_val, str):
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S%z"):
            try:
                # Handle standard formats
                clean_val = dt_val.replace("Z", "+00:00") if "Z" in dt_val else dt_val
                if "%z" in fmt or "+00:00" in clean_val:
                    return datetime.fromisoformat(clean_val).replace(tzinfo=None)
                return datetime.strptime(clean_val, fmt)
            except (ValueError, TypeError):
                continue
    return None


def fn_validate_donor_eligibility(
    donor: Dict[str, Any],
    donation_history: List[Dict[str, Any]],
    donation_type: str = "WHOLE_BLOOD",
    target_date: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Evaluates rolling donor eligibility.
    Matches PostgreSQL function bdcn_core.fn_validate_donor_eligibility logic.
    """
    eval_date = parse_datetime(target_date) or datetime.utcnow()
    donation_type = donation_type.upper()

    if not donor:
        return {
            "isEligible": False,
            "daysRemaining": -1,
            "nextEligibleDate": None,
            "blockReason": "DONOR_NOT_FOUND"
        }

    # 1. Check Medical Deferrals
    is_deferred = donor.get("is_deferred", False)
    deferral_end_date = parse_datetime(donor.get("deferral_end_date"))
    deferral_reason = donor.get("deferral_reason") or "ACTIVE_MEDICAL_DEFERRAL"

    if is_deferred:
        if deferral_end_date and eval_date >= deferral_end_date:
            # Deferral has passed
            pass
        else:
            days_rem = (deferral_end_date.date() - eval_date.date()).days if deferral_end_date else 9999
            return {
                "isEligible": False,
                "daysRemaining": max(days_rem, 1),
                "nextEligibleDate": deferral_end_date.strftime("%Y-%m-%dT00:00:00Z") if deferral_end_date else None,
                "blockReason": deferral_reason
            }

    # 2. Check Required Interval
    required_days = INTERVAL_DAYS.get(donation_type, 28)

    # Filter donation events for this donation type
    matching_events = [
        e for e in donation_history
        if e.get("donation_type", "").upper() == donation_type
    ]
    
    # Sort descending by collected_at
    matching_events.sort(
        key=lambda e: parse_datetime(e.get("collected_at")) or datetime.min,
        reverse=True
    )

    if not matching_events:
        return {
            "isEligible": True,
            "daysRemaining": 0,
            "nextEligibleDate": eval_date.strftime("%Y-%m-%dT00:00:00Z"),
            "blockReason": "ELIGIBLE_FIRST_TIME"
        }

    latest_event = matching_events[0]
    last_donation_date = parse_datetime(latest_event.get("collected_at"))

    if not last_donation_date:
        return {
            "isEligible": True,
            "daysRemaining": 0,
            "nextEligibleDate": eval_date.strftime("%Y-%m-%dT00:00:00Z"),
            "blockReason": "ELIGIBLE"
        }

    # Check platelet yearly volume limit
    if donation_type == "PLATELETS":
        one_year_ago = eval_date - timedelta(days=365)
        past_year_platelets = [
            e for e in matching_events
            if (parse_datetime(e.get("collected_at")) or datetime.min) >= one_year_ago
        ]
        if len(past_year_platelets) >= MAX_PLATELET_ANNUAL_LIMIT:
            oldest_in_window = min(parse_datetime(e.get("collected_at")) for e in past_year_platelets)
            next_free = oldest_in_window + timedelta(days=366)
            return {
                "isEligible": False,
                "daysRemaining": (next_free.date() - eval_date.date()).days,
                "nextEligibleDate": next_free.strftime("%Y-%m-%dT00:00:00Z"),
                "blockReason": "ANNUAL_PLATELET_DONATION_CAP_REACHED"
            }

    next_eligible_dt = last_donation_date + timedelta(days=required_days)
    days_diff = (eval_date.date() - last_donation_date.date()).days

    if days_diff >= required_days:
        return {
            "isEligible": True,
            "daysRemaining": 0,
            "nextEligibleDate": next_eligible_dt.strftime("%Y-%m-%dT00:00:00Z"),
            "blockReason": "ELIGIBLE"
        }
    else:
        days_remaining = required_days - days_diff
        return {
            "isEligible": False,
            "daysRemaining": days_remaining,
            "nextEligibleDate": next_eligible_dt.strftime("%Y-%m-%dT00:00:00Z"),
            "blockReason": "MINIMUM_DONATION_INTERVAL_NOT_MET"
        }
