# Changelog

## [Unreleased]

### Added
- **[ARCH-4675]** UI Pages + Requirements: Emergency Blood Donor Connection & Real-Time Dispatch Network Platform
  - *Key modifications:*
    - `.env.example`
    - `docker-compose.yml`
    - `db/schema.sql`
    - `db/seed.sql`
    - `db/init_db.py`
    - `templates/donor_portal_login.html`
    - `templates/donor_emergency_response.html`
    - `templates/donor_check_in_pass.html`
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
