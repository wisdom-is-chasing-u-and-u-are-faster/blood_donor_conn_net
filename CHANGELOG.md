# Changelog

## [Unreleased]

### Added
- **[ARCH-578]** UI Pages + Requirements: Blood Donor Connection Network (BDCN)
  - *Key modifications:*
    - `app.py`
    - `tests/test_app.py`
    - `templates/admin_dashboard.html`
    - `templates/donor_dashboard.html`
    - `templates/alert_view.html`
    - `templates/landing.html`
    - `templates/login.html`
    - `templates/request_form.html`
### Fixed
- **[ARCH-406]** ARCH-BUG1: Fix Geolocation Clustering Precision Leak on Mobile Client Map View
  - *Key modifications:*
    - `app.py`
    - `tests/test_app.py`
### Added
- **[ARCH-405]** ARCH-S1: Recipient Request Submission & Validation Engine
  - *Key modifications:*
    - `app.py`
    - `tests/test_app.py`
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
