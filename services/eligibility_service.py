"""
Eligibility service module for Blood Donor Connection Network (BDCN).
Evaluates donor age, weight, and donation interval criteria for compliance.
"""
from datetime import datetime, date
from typing import Dict, Any, List, Optional


MIN_DONOR_AGE = 18
MAX_DONOR_AGE = 65
MIN_DONOR_WEIGHT_KG = 50.0
MIN_DONATION_INTERVAL_DAYS = 90  # Standard clinical cool-off interval


def calculate_days_since_donation(last_donation_val: Any) -> Optional[int]:
    """Calculate days elapsed since last donation date."""
    if not last_donation_val:
        return None

    if isinstance(last_donation_val, (datetime, date)):
        last_date = last_donation_val if isinstance(last_donation_val, date) else last_donation_val.date()
    elif isinstance(last_donation_val, str):
        try:
            # support ISO format YYYY-MM-DD
            last_date = datetime.strptime(last_donation_val.strip(), "%Y-%m-%d").date()
        except ValueError:
            try:
                last_date = datetime.fromisoformat(last_donation_val.strip()).date()
            except Exception:
                return None
    else:
        return None

    today = date.today()
    delta = (today - last_date).days
    return max(0, delta)


def evaluate_donor_eligibility(
    age: int,
    weight: float,
    last_donation_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate donor eligibility based on clinical and regulatory criteria:
    - Age must be between 18 and 65 years.
    - Weight must be at least 50 kg.
    - Donation interval must be at least 90 days if previously donated.

    Returns dict with is_eligible (bool), message (str), and reasons (list).
    """
    reasons: List[str] = []

    # Age check
    if age < MIN_DONOR_AGE or age > MAX_DONOR_AGE:
        reasons.append(
            f"Donors must be between {MIN_DONOR_AGE} and {MAX_DONOR_AGE} years old."
        )

    # Weight check
    if weight < MIN_DONOR_WEIGHT_KG:
        reasons.append(
            f"Minimum weight requirement is {int(MIN_DONOR_WEIGHT_KG)}kg."
        )

    # Donation interval check
    days_since = calculate_days_since_donation(last_donation_date)
    if days_since is not None and days_since < MIN_DONATION_INTERVAL_DAYS:
        reasons.append(
            f"You must wait at least {MIN_DONATION_INTERVAL_DAYS} days between donations. "
            f"Your last donation was {days_since} days ago."
        )

    is_eligible = len(reasons) == 0
    if is_eligible:
        message = "Congratulations! You are eligible to donate blood."
    else:
        message = "You are not eligible to donate. " + " ".join(reasons)

    return {
        "is_eligible": is_eligible,
        "message": message,
        "reasons": reasons,
        "days_since_donation": days_since,
    }
