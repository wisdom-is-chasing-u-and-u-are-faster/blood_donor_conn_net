# Changelog

## [Unreleased]

### Added

- **feat(ARCH-7525): Donor Eligibility & Biological Cooldown Verification Engine**
  - Implemented high-throughput REST endpoint `GET /api/donors/{donor_id}/eligibility` in `app/routers/donors.py` enforcing statutory 56-day whole-blood biological cooldown period.
  - Architected Pydantic V2 schema `DonorEligibilityResponse` in `app/models.py` with immutable serialization and zero PII leakage.
  - Implemented defensive boundary validation guarding against future-dated donation records (HTTP 400 `TEMPORAL_ANOMALY_FUTURE_DATE`).
  - Added support for first-time donors with null historical donation dates (`last_donation_date is None`).
  - Added donation cooldown check in matching flow before assigning donors to blood requests.
  - Added 18 comprehensive automated Gherkin test scenarios in `tests/test_eligibility.py` achieving 100% test pass rate.

### Added

- **feat(ARCH-3357): UI Pages + Requirements: Blood Donor Connection Network (BDCN) Core Platform**

  This change introduces the initial front-end implementation of the Blood Donor Connection Network (BDCN) Core Platform. The key deliverables of this PR are:

  - A Flask-based Python application (`app.py`) to handle routing, session management, and the core application logic.
  - A set of HTML templates using Bootstrap 5 for various user interfaces, including:
    - Hospital and administrator login portals.
    - A dashboard for hospital staff to view and manage blood demands.
    - A form for creating new blood demand requests.
    - An administrative queue for verifying and processing pending requests.
    - Pages for managing alerts and viewing audit logs.
  - The `requirements.txt` file, specifying the project's dependencies (Flask and pytest).
  - A suite of verification tests (`tests/test_app.py`) to ensure the basic functionality of the application.
