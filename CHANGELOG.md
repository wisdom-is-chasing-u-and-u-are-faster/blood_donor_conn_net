# Changelog

## [Unreleased]

### Added
- **[ARCH-7105]** UI Pages + Requirements: Donor Eligibility and Urgent Matching UI
  - *Key modifications:*
    - `requirements.txt`
    - `services/__init__.py`
    - `services/eligibility_service.py`
    - `services/matching_service.py`
    - `templates/pre_screening.html`
    - `templates/dashboard.html`
    - `templates/base.html`
    - `app.py`
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
