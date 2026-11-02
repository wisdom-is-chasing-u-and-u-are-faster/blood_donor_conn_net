# Changelog

## [Unreleased]

### Added
- **feat(ARCH-6803): UI Pages + Requirements: Blood Donor Connection Network (BDCN)**
  - Implemented multi-provider social authentication (Google, Apple, Facebook) supporting Donor, Recipient, and Admin roles (`POST /api/v1/auth/social`).
  - Implemented digital document upload verification for recipients (`POST /api/v1/verifications/upload`).
  - Added district administrator verification queue and action review (`GET /api/v1/admin/verifications`, `POST /api/v1/admin/verifications/<id>/action`).
  - Added donor hotspot density clustering map API (`GET /api/v1/donors/hotspots`) with privacy-first coarse centroid coordinate obfuscation and unverified recipient lockout.
  - Added secure in-system notification and messaging center (`GET /api/v1/messages`, `POST /api/v1/messages/send`) with contact initiation locked until recipient verification is approved.
  - Added social sharing APIs for badges and milestones (`POST /api/v1/achievements/share`).
  - Added 11 Variant A self-contained UI screen templates with client API module wiring (`static/js/api.js`).
  - Added 12-factor configuration (`.env.example`, `docker-compose.yml`), ANSI SQL schema & seeds (`db/schema.sql`, `db/seed.sql`, `db/init_db.py`), and cross-platform mobile shells (`mobile/ios`, `mobile/android`).

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
