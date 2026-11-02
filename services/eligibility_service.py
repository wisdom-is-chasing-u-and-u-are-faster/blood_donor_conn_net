"""
Eligibility Service for Blood Donor Pre-Screening.
Enforces clinical eligibility criteria:
- Age: 18 - 65 inclusive (REQ-F-003)
- Weight: >= 50kg (REQ-F-004)
- Donation intervals: >= 56 days for males, >= 90 days for females (REQ-F-005)
- Health questionnaire & declaration validation (REQ-F-006)
"""
from datetime import datetime, date
from typing import Dict, Any, List, Tuple


def calculate_age(dob: date, reference_date: date = None) -> int:
    """Calculate age from date of birth."""
    if reference_date is None:
        reference_date = date.today()
    age = reference_date.year - dob.year
    if (reference_date.month, reference_date.day) < (dob.month, dob.day):
        age -= 1
    return age


def evaluate_eligibility(data: Dict[str, Any], reference_date: date = None) -> Dict[str, Any]:
    """
    Evaluates donor eligibility based on clinical pre-screening criteria.
    Returns:
        {
            "eligible": bool,
            "reasons": List[str],
            "details": Dict[str, Any]
        }
    """
    if reference_date is None:
        reference_date = date.today()

    reasons: List[str] = []
    details: Dict[str, Any] = {}

    # 1. Parse Date of Birth & Validate Age (REQ-F-003: 18 to 65 inclusive)
    dob_raw = data.get("dob")
    if not dob_raw:
        reasons.append("Date of birth is required.")
        age = None
    else:
        if isinstance(dob_raw, str):
            try:
                dob = datetime.strptime(dob_raw.strip(), "%Y-%m-%d").date()
            except ValueError:
                dob = None
                reasons.append("Invalid date of birth format. Use YYYY-MM-DD.")
        elif isinstance(dob_raw, (datetime, date)):
            dob = dob_raw if isinstance(dob_raw, date) else dob_raw.date()
        else:
            dob = None

        if dob:
            age = calculate_age(dob, reference_date)
            details["age"] = age
            if age < 18 or age > 65:
                reasons.append(f"Donor age must be between 18 and 65 inclusive (current age: {age}).")
        else:
            age = None

    # 2. Validate Weight (REQ-F-004: >= 50kg)
    weight_raw = data.get("weight")
    if weight_raw is None:
        reasons.append("Weight is required.")
    else:
        try:
            weight = float(weight_raw)
            details["weight"] = weight
            if weight < 50.0:
                reasons.append(f"Donor weight must be at least 50kg (current weight: {weight}kg).")
        except (ValueError, TypeError):
            reasons.append("Invalid weight value. Must be a numeric quantity in kg.")

    # 3. Validate Donation Intervals (REQ-F-005: 56 days for males, 90 days for females)
    gender = (data.get("gender") or "").strip().lower()
    last_donation_raw = data.get("last_donation_date") or data.get("last_donation")
    
    if last_donation_raw:
        if isinstance(last_donation_raw, str):
            try:
                last_donation = datetime.strptime(last_donation_raw.strip(), "%Y-%m-%d").date()
            except ValueError:
                last_donation = None
                reasons.append("Invalid last donation date format. Use YYYY-MM-DD.")
        elif isinstance(last_donation_raw, (datetime, date)):
            last_donation = last_donation_raw if isinstance(last_donation_raw, date) else last_donation_raw.date()
        else:
            last_donation = None

        if last_donation:
            days_since = (reference_date - last_donation).days
            details["days_since_donation"] = days_since
            min_interval = 90 if gender == "female" else 56
            if days_since < min_interval:
                reasons.append(
                    f"Minimum donation interval not met: {days_since} days elapsed since last donation, "
                    f"required: {min_interval} days for {gender or 'male'} donors."
                )

    # 4. Health Declaration & Questionnaire (REQ-F-006)
    if data.get("health_fever_48h") is True or str(data.get("health_fever_48h")).lower() in ["yes", "true", "1"]:
        reasons.append("Donor reported fever or feeling unwell in the last 48 hours.")
    
    if data.get("health_malaria_6m") is True or str(data.get("health_malaria_6m")).lower() in ["yes", "true", "1"]:
        reasons.append("Donor reported travel to malaria-risk area in the last 6 months.")

    declaration_agreed = data.get("declaration_agreed")
    if declaration_agreed is not True and str(declaration_agreed).lower() not in ["true", "yes", "1", "on"]:
        reasons.append("Donor must agree to the health and accuracy declaration.")

    eligible = len(reasons) == 0
    return {
        "eligible": eligible,
        "reasons": reasons,
        "details": details
    }
