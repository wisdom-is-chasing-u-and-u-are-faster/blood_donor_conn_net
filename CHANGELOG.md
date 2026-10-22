# Changelog

## [Unreleased]

## [Unreleased] - ARCH-5309 - 2026-10-22
### Added
- Implemented high-fidelity self-contained UI pages from Variant-A design mockup for Login, Signup, Donor Dashboard, Donor Profile, Request Submission, Admin Dashboard, Request Details, and Secure Anonymized Messaging.
- Added comprehensive REST API endpoints under /api/v1 for authentication (/auth/signup, /auth/login, /auth/social), donor management (/donors/profile, /donors/availability), recipient blood requests (/requests, /requests/<id>), administrative actions (/admin/requests/<id>/action), pledges (/requests/<id>/pledge), and secure messaging (/messages).
- Integrated 12-factor configuration (.env.example, docker-compose.yml) and relational SQLite schema/seed assets (db/schema.sql, db/seed.sql, db/init_db.py).
- Created client-side API bridge in public/js/api.js and static/js/api.js.
- Added comprehensive automated test suite in tests/test_bdcn_features.py with 100% pass rate and zero regressions.


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
