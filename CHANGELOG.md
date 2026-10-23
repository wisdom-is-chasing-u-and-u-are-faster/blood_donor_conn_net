# Changelog

## [Unreleased]

### Added

- **feat(ARCH-5400): UI Pages + Requirements: Blood Donor Connection Network (BDCN)**

  Implemented software features and high-fidelity Variant-A UI screens for Blood Donor Connection Network:
  - Added OAuth2 / Social authentication endpoints for Google, Apple, and Facebook (`/api/v1/auth/social`).
  - Added recipient blood request creation with medical requisition document upload and administrative review queue (`/api/v1/requests`).
  - Added H3 hexagonal spatial clustering for privacy preservation, ensuring raw GPS coordinates and precise residential addresses are never stored or transmitted.
  - Implemented District Administrator adjudication workflow (`/api/v1/admin/adjudicate`) with immutable audit logging and automated push notification broadcast to donor clusters.
  - Added mandatory cool-off period enforcement (56 days for Whole Blood, 14 days for Platelets) upon logging donations (`/api/v1/donations/log`).
  - Added gamification achievements and badges engine (`/api/v1/gamification/badges`).
  - Scaffolded ANSI SQL relational schema (`db/schema.sql`), baseline seeds (`db/seed.sql`), database initializer (`db/init_db.py`), 12-factor configuration (`.env.example`, `docker-compose.yml`), client API wrapper (`static/js/api.js`), and comprehensive pytest suite (`tests/test_arch5400.py`).

- **feat(ARCH-3357): UI Pages + Requirements: Blood Donor Connection Network (BDCN) Core Platform**

  This change introduces the initial front-end implementation of the Blood Donor Connection Network (BDCN) Core Platform.
