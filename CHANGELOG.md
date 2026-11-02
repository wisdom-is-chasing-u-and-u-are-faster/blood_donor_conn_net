# Changelog

## [Unreleased]

## [Unreleased] - 2026-11-02
### Added
- Donor eligibility pre-screening service (services/eligibility_service.py) enforcing age (18-65), weight (>=50kg), donation intervals (56d male / 90d female), and health declaration (REQ-F-001 - REQ-F-006).
- Urgent blood request compatibility matching service (services/matching_service.py) using in-memory clinical ABO/Rh compatibility matrix with LRU cache and verified donor filter (REQ-F-007, REQ-F-008, CONSTRAINT-002).
- REST API endpoints (/health, /api/v1/prescreening/evaluate, /api/v1/donors/urgent-match, /api/v1/donors, /api/v1/transactions) with Idempotency-Key and Operator role enforcement (REQ-F-009 - REQ-F-013).
- Relational schema and initial seeds (db/schema.sql, db/seed.sql) with composite index on (blood_group, is_verified, current_status) (CONSTRAINT-003, CONSTRAINT-004).
- 12-factor configuration (.env.example, docker-compose.yml) for containerized execution.
- High-fidelity interactive UI screens and client API helper (public/js/api.js, urgent_request_dashboard.html, donor_pre_screening_form.html, donor_directory.html).
- 18 INVEST-grade BDD Gherkin test scenarios in tests/test_donor_features.py (REQ-N-004).

### Changed
- Monolithic app.py refactored into modular service architecture (CONSTRAINT-001, REQ-N-001).


## [Unreleased]

## [Unreleased] - 2026-11-02
### Added
- Donor eligibility pre-screening service (services/eligibility_service.py) enforcing age (18-65), weight (>=50kg), donation intervals (56d male / 90d female), and health declaration (REQ-F-001 - REQ-F-006).
- Urgent blood request compatibility matching service (services/matching_service.py) using in-memory clinical ABO/Rh compatibility matrix with LRU cache and verified donor filter (REQ-F-007, REQ-F-008, CONSTRAINT-002).
- REST API endpoints (/health, /api/v1/prescreening/evaluate, /api/v1/donors/urgent-match, /api/v1/donors, /api/v1/transactions) with Idempotency-Key and Operator role enforcement (REQ-F-009 - REQ-F-013).
- Relational schema and initial seeds (db/schema.sql, db/seed.sql) with composite index on (blood_group, is_verified, current_status) (CONSTRAINT-003, CONSTRAINT-004).
- 12-factor configuration (.env.example, docker-compose.yml) for containerized execution.
- High-fidelity interactive UI screens and client API helper (public/js/api.js, urgent_request_dashboard.html, donor_pre_screening_form.html, donor_directory.html).
- 18 INVEST-grade BDD Gherkin test scenarios in tests/test_donor_features.py (REQ-N-004).

### Changed
- Monolithic app.py refactored into modular service architecture (CONSTRAINT-001, REQ-N-001).
 - 2026-11-02
### Added
- Donor eligibility pre-screening service () enforcing age (18-65), weight (>=50kg), donation intervals (56d male / 90d female), and health declaration (REQ-F-001 - REQ-F-006).
- Urgent blood request compatibility matching service () using in-memory clinical ABO/Rh compatibility matrix with LRU cache and verified donor filter (REQ-F-007, REQ-F-008, CONSTRAINT-002).
- REST API endpoints (, , , , ) with Idempotency-Key and Operator role enforcement (REQ-F-009 - REQ-F-013).
- Relational schema and initial seeds (, ) with composite index on  (CONSTRAINT-003, CONSTRAINT-004).
- 12-factor configuration (, ) for containerized execution.
- High-fidelity interactive UI screens and client API helper (, , , ).
- 18 INVEST-grade BDD Gherkin test scenarios in  (REQ-N-004).

### Changed
- Monolithic  refactored into modular service architecture (CONSTRAINT-001, REQ-N-001).


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
